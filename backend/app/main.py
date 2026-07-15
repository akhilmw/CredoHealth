from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.repositories import get_patient, list_patients
from app.schemas import MigrationResult, PatientDetailRead, PatientRead
from app.services import run_migration


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Credo Health FHIR Migration",
    lifespan=lifespan,
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/migration/run", response_model=MigrationResult)
def migrate_patients(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    # Starts a small FHIR migration from HAPI into the local SQLite database.
    return run_migration(db, limit)


@app.get("/patients", response_model=list[PatientRead])
def read_patients(db: Session = Depends(get_db)):
    # Lists migrated patients for the frontend patient list.
    return list_patients(db)


@app.get("/patients/{patient_id}", response_model=PatientDetailRead)
def read_patient(patient_id: int, db: Session = Depends(get_db)):
    # Returns one migrated patient with associated observations.
    patient = get_patient(db, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient
