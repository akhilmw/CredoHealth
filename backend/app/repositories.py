"""Database access helpers for patients and observations."""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models import Observation, Patient


# Creates or updates a patient using the stable source-system FHIR id.
def upsert_patient(db: Session, patient_data: dict) -> Patient:
    patient = db.scalar(
        select(Patient).where(Patient.fhir_id == patient_data["fhir_id"])
    )

    if patient is None:
        patient = Patient(**patient_data)
        db.add(patient)
    else:
        for field, value in patient_data.items():
            setattr(patient, field, value)

    db.flush()
    return patient


# Replaces a patient's observations with the latest migrated source snapshot.
def replace_patient_observations(
    db: Session,
    patient: Patient,
    observations_data: list[dict],
) -> int:
    db.execute(delete(Observation).where(Observation.patient_id == patient.id))

    observations = [
        Observation(patient_id=patient.id, **observation_data)
        for observation_data in observations_data
    ]
    db.add_all(observations)
    db.flush()

    return len(observations)


# Returns patients in database insertion order for the list API.
def list_patients(db: Session) -> list[Patient]:
    return list(db.scalars(select(Patient).order_by(Patient.id)))


# Loads one patient and its observations for the detail API.
def get_patient(db: Session, patient_id: int) -> Patient | None:
    return db.scalar(
        select(Patient)
        .where(Patient.id == patient_id)
        .options(selectinload(Patient.observations))
    )
