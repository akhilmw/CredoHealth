from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.repositories import get_patient, list_patients
from app.services import run_migration


class FakeFHIRClient:
    def __init__(self, fail_observations_for: str | None = None):
        self.fail_observations_for = fail_observations_for

    def fetch_patients(self, limit: int):
        return [
            {
                "resourceType": "Patient",
                "id": "patient-1",
                "name": [{"family": "Ramirez", "given": ["Carlos"]}],
                "gender": "male",
                "birthDate": "1974-05-12",
            },
            {
                "resourceType": "Patient",
                "id": "patient-2",
                "name": [{"family": "Nguyen", "given": ["Ava"]}],
                "gender": "female",
                "birthDate": "1985-07-09",
            },
        ][:limit]

    def fetch_observations_for_patient(self, patient_fhir_id: str):
        if patient_fhir_id == self.fail_observations_for:
            raise RuntimeError("observation fetch failed")

        return [
            {
                "resourceType": "Observation",
                "id": f"observation-{patient_fhir_id}",
                "status": "final",
                "code": {
                    "coding": [
                        {
                            "code": "4548-4",
                            "display": "Hemoglobin A1c",
                        }
                    ]
                },
                "valueQuantity": {"value": 9.4, "unit": "%"},
            }
        ]


def make_db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return SessionLocal()


# Verifies that a successful migration persists patients and observations.
def test_run_migration_saves_patients_and_observations():
    db = make_db_session()

    result = run_migration(db, limit=2, fhir_client=FakeFHIRClient())

    patients = list_patients(db)
    first_patient = get_patient(db, patients[0].id)
    assert result.patients_seen == 2
    assert result.patients_saved == 2
    assert result.observations_saved == 2
    assert result.failures == []
    assert len(patients) == 2
    assert first_patient is not None
    assert len(first_patient.observations) == 1

    db.close()


# Verifies that one patient failure is recorded without stopping later patients.
def test_run_migration_records_failure_and_continues():
    db = make_db_session()

    result = run_migration(
        db,
        limit=2,
        fhir_client=FakeFHIRClient(fail_observations_for="patient-1"),
    )

    patients = list_patients(db)
    assert result.patients_seen == 2
    assert result.patients_saved == 1
    assert result.observations_saved == 1
    assert len(result.failures) == 1
    assert "patient-1" in result.failures[0]
    assert [patient.fhir_id for patient in patients] == ["patient-2"]

    db.close()
