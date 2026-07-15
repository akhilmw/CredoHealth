# Credo Health Migration Plan

## Scope

This plan describes how I would migrate approximately 50,000 FHIR R4 `Patient` resources and their associated `Observation` resources from a legacy FHIR API into a new internal service. The working implementation in this repository is intentionally a small local slice; this document describes the production-minded approach.

## 1. Overall Approach

I would run the migration as an idempotent batch job rather than as a request/response web flow. The job would page through `Patient` resources from the source FHIR API, transform each resource into the internal schema, persist it, then fetch and persist related `Observation` resources for that patient.

The migration would track progress in a `migration_runs` table and a per-resource status table. Each source resource would be keyed by its stable FHIR id, allowing safe retries and re-runs without creating duplicates.

```text
FHIR API
  -> paginated Patient fetch
  -> Patient mapper
  -> internal Patient upsert
  -> Observation fetch by subject
  -> Observation mapper
  -> internal Observation upsert/replace
  -> validation and reconciliation report
```

Reliability considerations:

- Use FHIR pagination by following Bundle `link[relation="next"]`.
- Checkpoint after each page or patient batch so the job can resume after failure.
- Make writes idempotent with source FHIR ids and unique constraints.
- Commit in small batches, such as 100-500 patients, to avoid one large transaction.
- Treat patient-level failures as recoverable and continue processing other patients.

Observability:

- Emit structured logs with `migration_run_id`, source resource type, FHIR id, page URL, status, and error category.
- Track metrics for patients fetched, patients saved, observations fetched, observations saved, retries, failures, and duration.
- Produce a final reconciliation summary for source counts, destination counts, and failed resource ids.

API limits and performance:

- Use `_count` to request a reasonable page size, such as 100-500 depending on source behavior.
- Limit concurrent Observation fetches with a bounded worker pool to avoid overwhelming the source API.
- Use exponential backoff with jitter for transient failures.
- Retry network errors, timeouts, and 5xx responses. Do not retry most 4xx responses because they usually indicate a bad request or missing resource.
- Respect `Retry-After` if returned by the source system.

Error handling:

- Classify errors as transient, permanent, mapping, validation, or persistence failures.
- Store failed resource ids and error messages for replay.
- Continue the migration when individual patients or observations fail.
- Fail the full run only for systemic issues, such as invalid credentials, database outage, or repeated source API unavailability.

## 2. Data Mapping

The internal model should store only fields needed by the application, not the full FHIR payload.

### Patient

FHIR fields:

- `id`
- `name[0].given[0]`
- `name[0].family`
- `gender`
- `birthDate`
- `meta.lastUpdated`

Internal fields:

- `fhir_id`
- `given_name`
- `family_name`
- `gender`
- `birth_date`
- `source_updated_at`

The mapper should tolerate missing optional fields because real FHIR resources often contain partial data.

### Observation

FHIR fields:

- `id`
- `code.coding[0].code`
- `code.coding[0].display`
- `status`
- `effectiveDateTime`
- `valueQuantity.value`
- `valueQuantity.unit`

Internal fields:

- `fhir_id`
- `patient_id`
- `code`
- `display`
- `value`
- `unit`
- `status`
- `effective_at`

The mapper should support common FHIR value variants such as `valueQuantity`, `valueString`, `valueCode`, `valueBoolean`, `valueInteger`, and `valueCodeableConcept`.

## 3. Validation

I would validate the migration at three levels.

Record counts:

- Count source Patients from the FHIR search result metadata when available.
- Count destination Patients by `migration_run_id` or source system.
- Count Observations fetched and saved per patient.

Data correctness:

- Sample migrated records and compare source fields to internal fields.
- Validate required internal fields such as `fhir_id`.
- Validate date parsing and value/unit mapping.
- Use automated tests for representative FHIR resources and missing-field cases.

Failure reconciliation:

- Maintain a table of failed resource ids with error reason and retry status.
- Produce a final report listing successful records, failed records, skipped records, and retryable failures.
- Re-run only failed resources after fixes instead of restarting the full migration.

Consistency:

- Enforce uniqueness on source FHIR ids.
- Compare source and destination ids after migration.
- For each migrated Patient, verify expected Observation records were fetched and persisted.

## 4. Safety

In production, this data may contain PHI, so the migration must treat all clinical data as sensitive.

Secure storage:

- Encrypt data at rest using managed database encryption.
- Encrypt data in transit with TLS.
- Store secrets in a secret manager, not in code or local files.

Access controls:

- Restrict migration execution to authorized operators.
- Use least-privilege database credentials.
- Separate read access to the source system from write access to the destination.

Logging:

- Do not log names, addresses, identifiers, observation values, or raw FHIR payloads.
- Log only operational metadata such as resource type, source id, run id, and error category.
- Ensure logs are retained according to compliance requirements.

Operational safety:

- Use synthetic data in local development.
- Run a dry-run mode before writing production data.
- Validate against a staging destination before production.

## 5. Rollback and Recovery

The safest rollback strategy is to make each migration run identifiable and reversible.

Rollback approach:

- Add `migration_run_id` or source-system metadata to migrated rows.
- Use upserts keyed by FHIR id so a re-run updates existing rows rather than duplicating them.
- For a failed run, delete or mark inactive records associated with that run if they are not yet visible to users.
- If records are already visible, prefer a compensating migration that restores the previous version rather than destructive deletion.

Recovery approach:

- Checkpoint progress after each page or patient batch.
- Resume from the last successful page or from the failed-resource table.
- Retry transient failures automatically.
- Replay permanent failures only after mapper, data, or source issues are fixed.

This gives the migration predictable restart behavior while keeping partial success visible and auditable.
