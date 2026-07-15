from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Observation
from app.repositories import (
    get_patient,
    list_patients,
    replace_patient_observations,
    upsert_patient,
)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Verifies that upsert_patient inserts a new Patient row.
def test_upsert_patient_creates_patient(db_session):
    patient = upsert_patient(
        db_session,
        {
            "fhir_id": "patient-1",
            "given_name": "Carlos",
            "family_name": "Ramirez",
            "gender": "male",
            "birth_date": date(1974, 5, 12),
            "source_updated_at": None,
        },
    )

    assert patient.id is not None
    assert patient.fhir_id == "patient-1"
    assert list_patients(db_session) == [patient]


# Verifies that upsert_patient updates an existing Patient by FHIR id.
def test_upsert_patient_updates_existing_patient(db_session):
    patient = upsert_patient(
        db_session,
        {
            "fhir_id": "patient-1",
            "given_name": "Carlos",
            "family_name": "Ramirez",
            "gender": "male",
            "birth_date": date(1974, 5, 12),
            "source_updated_at": None,
        },
    )

    updated = upsert_patient(
        db_session,
        {
            "fhir_id": "patient-1",
            "given_name": "Carlo",
            "family_name": "R.",
            "gender": "male",
            "birth_date": date(1974, 5, 12),
            "source_updated_at": None,
        },
    )

    assert updated.id == patient.id
    assert updated.given_name == "Carlo"
    assert len(list_patients(db_session)) == 1


# Verifies that replacing observations removes old rows before inserting new rows.
def test_replace_patient_observations_replaces_existing_rows(db_session):
    patient = upsert_patient(
        db_session,
        {
            "fhir_id": "patient-1",
            "given_name": "Carlos",
            "family_name": "Ramirez",
            "gender": "male",
            "birth_date": date(1974, 5, 12),
            "source_updated_at": None,
        },
    )
    replace_patient_observations(
        db_session,
        patient,
        [
            {
                "fhir_id": "observation-1",
                "code": "4548-4",
                "display": "Hemoglobin A1c",
                "value": "9.4",
                "unit": "%",
                "status": "final",
                "effective_at": None,
            }
        ],
    )

    inserted_count = replace_patient_observations(
        db_session,
        patient,
        [
            {
                "fhir_id": "observation-2",
                "code": "2345-7",
                "display": "Glucose",
                "value": "268",
                "unit": "mg",
                "status": "final",
                "effective_at": None,
            }
        ],
    )

    observations = list(db_session.query(Observation).all())
    assert inserted_count == 1
    assert len(observations) == 1
    assert observations[0].fhir_id == "observation-2"


# Verifies that get_patient returns a Patient with observations loaded.
def test_get_patient_loads_observations(db_session):
    patient = upsert_patient(
        db_session,
        {
            "fhir_id": "patient-1",
            "given_name": "Carlos",
            "family_name": "Ramirez",
            "gender": "male",
            "birth_date": date(1974, 5, 12),
            "source_updated_at": None,
        },
    )
    replace_patient_observations(
        db_session,
        patient,
        [
            {
                "fhir_id": "observation-1",
                "code": "4548-4",
                "display": "Hemoglobin A1c",
                "value": "9.4",
                "unit": "%",
                "status": "final",
                "effective_at": None,
            }
        ],
    )
    db_session.expire_all()

    found = get_patient(db_session, patient.id)

    assert found is not None
    assert found.fhir_id == "patient-1"
    assert len(found.observations) == 1
