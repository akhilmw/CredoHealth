from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.repositories import replace_patient_observations, upsert_patient


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app), SessionLocal
    finally:
        app.dependency_overrides.clear()


def seed_patient_with_observation(SessionLocal):
    db = SessionLocal()
    patient = upsert_patient(
        db,
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
        db,
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
    db.commit()
    patient_id = patient.id
    db.close()
    return patient_id


# Verifies that the list endpoint returns persisted patients.
def test_read_patients_returns_patient_list(client):
    api_client, SessionLocal = client
    seed_patient_with_observation(SessionLocal)

    response = api_client.get("/patients")

    assert response.status_code == 200
    assert response.json()[0]["fhir_id"] == "patient-1"


# Verifies that the detail endpoint returns one patient with observations.
def test_read_patient_returns_patient_detail(client):
    api_client, SessionLocal = client
    patient_id = seed_patient_with_observation(SessionLocal)

    response = api_client.get(f"/patients/{patient_id}")

    assert response.status_code == 200
    assert response.json()["fhir_id"] == "patient-1"
    assert response.json()["observations"][0]["fhir_id"] == "observation-1"


# Verifies that unknown patient ids return a 404.
def test_read_patient_returns_404_for_missing_patient(client):
    api_client, _ = client

    response = api_client.get("/patients/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Patient not found"}
