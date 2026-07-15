"""Migration orchestration service."""

from sqlalchemy.orm import Session

from app.fhir_client import FHIRClient
from app.mappers import map_observation_resource, map_patient_resource
from app.repositories import replace_patient_observations, upsert_patient
from app.schemas import MigrationResult


def run_migration(
    db: Session,
    limit: int,
    fhir_client: FHIRClient | None = None,
) -> MigrationResult:
    fhir_client = fhir_client or FHIRClient()
    patient_resources = fhir_client.fetch_patients(limit)
    patients_seen = len(patient_resources)
    patients_saved = 0
    observations_saved = 0
    failures: list[str] = []

    # Commit each patient independently so one bad resource does not undo prior work.
    for patient_resource in patient_resources:
        patient_fhir_id = patient_resource.get("id", "unknown")
        try:
            # Transform FHIR resources before handing them to the repository layer.
            patient_data = map_patient_resource(patient_resource)
            patient = upsert_patient(db, patient_data)
            observation_resources = fhir_client.fetch_observations_for_patient(
                patient.fhir_id
            )
            observations_data = [
                map_observation_resource(resource)
                for resource in observation_resources
            ]

            count = replace_patient_observations(db, patient, observations_data)

            patients_saved += 1
            observations_saved += count
            db.commit()
        except Exception as exc:
            # Record the failure and continue so the migration reports partial success.
            db.rollback()
            failures.append(f"Patient {patient_fhir_id}: {exc}")

    return MigrationResult(
        patients_seen=patients_seen,
        patients_saved=patients_saved,
        observations_saved=observations_saved,
        failures=failures,
    )
