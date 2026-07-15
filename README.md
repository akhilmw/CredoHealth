# Credo Health FHIR Migration

Small full-stack take-home app that migrates synthetic FHIR R4 `Patient` and `Observation` data from the public HAPI FHIR sandbox into a local SQLite database.

The app includes:

- FastAPI backend
- SQLite persistence with SQLAlchemy
- React + Vite frontend
- Backend tests
- `Plan.md` production migration design

## Data Source

FHIR endpoint:

```text
https://hapi.fhir.org/baseR4
```

This project uses only the public HAPI FHIR sandbox and synthetic/demo data. Do not use real patient data or PHI with this local app.

## Backend Setup

From the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Run Backend

```bash
cd backend
./.venv/bin/uvicorn app.main:app --reload
```

Backend runs at:

```text
http://localhost:8000
```

API docs:

```text
http://localhost:8000/docs
```

The SQLite database is created automatically at:

```text
backend/credo_health.db
```

## Frontend Setup

From the repository root:

```bash
cd frontend
npm install
```

## Run Frontend

Start the backend first, then in a second terminal:

```bash
cd frontend
npm run dev
```

Frontend runs at:

```text
http://localhost:5173
```

The Vite dev server proxies `/api/*` requests to the FastAPI backend.

## Common Commands

Run backend tests:

```bash
cd backend
./.venv/bin/pytest
```

Type-check frontend:

```bash
cd frontend
npx tsc --noEmit
```

Build frontend:

```bash
cd frontend
npm run build
```

Run a small migration manually:

```bash
curl -X POST "http://localhost:8000/migration/run?limit=5"
```

List migrated patients:

```bash
curl "http://localhost:8000/patients"
```

Get patient detail:

```bash
curl "http://localhost:8000/patients/1"
```

## API Endpoints

- `GET /health` - health check
- `POST /migration/run?limit=5` - migrate a small batch of patients and observations
- `GET /patients` - list migrated patients
- `GET /patients/{patient_id}` - get one patient with observations

## Implementation Notes

The local implementation intentionally migrates small batches. The backend currently caps migration requests at 100 patients to avoid putting unnecessary load on the public HAPI sandbox.

Current flow:

```text
FastAPI route
  -> migration service
  -> FHIR client
  -> FHIR mappers
  -> repository layer
  -> SQLite
```

Patients are upserted by source FHIR id. Observations for a patient are replaced with the latest fetched snapshot during migration.

## AI Usage Disclosure

AI assistance was used to help scaffold the project, discuss architecture, implement portions of the backend and frontend, write tests, and draft documentation. I reviewed the generated code, ran tests/builds, and made implementation decisions throughout the process.

## What I Would Do Next

- Add full FHIR pagination by following Bundle `next` links.
- Add a migration run table with checkpoint/resume support.
- Add better progress reporting for long migrations.
- Add structured logging and metrics.
- Add Alembic migrations instead of startup `create_all()`.
- Add more Observation value type coverage and validation.
- Add frontend loading states per panel instead of one shared loading flag.
- Add Docker Compose for easier local startup.
