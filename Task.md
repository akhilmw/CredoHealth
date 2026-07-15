```markdown
# Credo Health - Full Stack Python Take Home Exercise

## Overview

This exercise is designed to mirror the kind of work a Full Stack Engineer at Credo Health would perform: migrating clinical data from an external healthcare system, transforming it into an internal data model, persisting it locally, and exposing it through a simple web application.

The expected time limit is approximately **3 hours**. The goal is **not** to build a production-ready application, but rather to demonstrate engineering judgment, clean code, sensible architecture, and thoughtful tradeoffs.

---

# Important

- Use **synthetic data only**.
- Do **not** use, upload, or store any real patient data or PHI.
- The exercise uses the public **HAPI FHIR R4 sandbox**.

FHIR Endpoint:

https://hapi.fhir.org/baseR4

The server is publicly accessible, requires no authentication, and may be reset periodically.

---

# Deliverables

The final submission should be a **public GitHub repository** containing:

- Backend source code
- Frontend source code
- `Plan.md`
- `README.md`

The README should include:

- Setup instructions
- Run instructions
- AI usage disclosure
- "What I would do next" section describing unfinished work or future improvements

---

# Part 1 - Plan.md

**Suggested Time:** ~45 minutes

Imagine migrating approximately **50,000 Patient records** and their associated **Observation resources** from a legacy clinical system exposed through a FHIR R4 API into a new internal service.

Create a **1–2 page design document** covering:

## 1. Overall Approach

Describe:

- Migration strategy
- Reliability considerations
- Observability
- Handling API limits
- Retry strategy
- Performance considerations
- Error handling

Pseudocode and architecture diagrams are encouraged.

---

## 2. Data Mapping

Explain how FHIR resources would be transformed into a simplified internal model.

Specifically discuss:

- Patient
- Observation

---

## 3. Validation

Explain how you would verify:

- Every record migrated successfully
- Data correctness
- Missing or failed records
- Consistency between source and destination

---

## 4. Safety

Describe how a production implementation would responsibly handle PHI, including:

- Secure storage
- Encryption
- Access controls
- Logging considerations

---

## 5. Rollback

Explain how the migration could safely recover if something fails midway.

---

# Part 2 - Working Slice

**Suggested Time:** ~2 hours

Build a small but functional implementation of the migration.

Use:

- Django **or your preferred Python backend framework**
- Vue **or your preferred frontend framework**

---

## Backend Requirements

The backend should:

- Fetch Patient records from the HAPI FHIR server
- Fetch each patient's associated Observation resources
- Transform them into a simplified internal schema
- Persist the data locally (SQLite is acceptable)
- Expose REST APIs to access the migrated data

Example endpoints:

- List patients
- Retrieve a single patient with associated observations

---

## Frontend Requirements

Build a minimal UI that allows:

- Viewing migrated patients
- Clicking a patient
- Viewing that patient's observations

Visual polish is **not** important.

---

# Required Features

Regardless of implementation choices, include:

- Graceful handling of external API failures
  - Retry
  - Backoff
  - Or other deliberate error handling

- A couple of meaningful backend tests

- README with:
  - Setup instructions
  - Run instructions
  - AI usage disclosure
  - Future work

---

# Explicitly Out of Scope

Do **not** spend time implementing:

- Authentication
- Authorization
- Deployment
- Hosting
- UI polish
- Pagination
- Real-time synchronization

The focus should remain on the migration workflow and backend architecture.

---

# AI Usage

AI tools (Claude, Copilot, ChatGPT, Codex, etc.) are explicitly allowed.

However:

- Clearly document where AI was used.
- Be able to explain every design decision and every line of code during a follow-up interview.

---

# Evaluation Criteria

The submission will primarily be evaluated on:

## Correctness

- Runs successfully
- Matches the requested functionality

## Code Quality

- Clean
- Readable
- Well structured
- Avoids unnecessary complexity

## API & Data Modeling

- Sensible REST endpoints
- Appropriate status codes
- Clean internal schema

## FHIR Handling

- Correctly navigates nested FHIR resources
- Simplifies them appropriately

## Robustness

- Handles failures gracefully
- Covers important edge cases

## Communication

- Clear README
- Thoughtful migration plan
- Production-minded reasoning

## Responsible Data Handling

- Demonstrates awareness of PHI and healthcare data considerations

---

# Submission Checklist

The GitHub repository should contain:

- Backend
- Frontend
- Plan.md
- README.md

README should include:

- Installation instructions
- Running instructions
- AI usage disclosure
- Future improvements / next steps

```
