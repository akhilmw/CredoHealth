from datetime import date

from app.mappers import map_observation_resource, map_patient_resource


def test_map_patient_resource_from_hapi_shape():
    resource = {
        "resourceType": "Patient",
        "id": "131896579",
        "meta": {
            "lastUpdated": "2026-04-10T15:55:37.648-04:00",
        },
        "name": [
            {
                "use": "official",
                "family": "Ramirez",
                "given": ["Carlos"],
            }
        ],
        "gender": "male",
        "birthDate": "1974-05-12",
    }

    mapped = map_patient_resource(resource)

    assert mapped["fhir_id"] == "131896579"
    assert mapped["given_name"] == "Carlos"
    assert mapped["family_name"] == "Ramirez"
    assert mapped["gender"] == "male"
    assert mapped["birth_date"] == date(1974, 5, 12)
    assert mapped["source_updated_at"] is not None


def test_map_patient_resource_handles_missing_optional_fields():
    resource = {
        "resourceType": "Patient",
        "id": "patient-1",
    }

    mapped = map_patient_resource(resource)

    assert mapped == {
        "fhir_id": "patient-1",
        "given_name": None,
        "family_name": None,
        "gender": None,
        "birth_date": None,
        "source_updated_at": None,
    }


def test_map_observation_resource_from_hapi_value_quantity_shape():
    resource = {
        "resourceType": "Observation",
        "id": "131896585",
        "status": "final",
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "4548-4",
                    "display": "Hemoglobin A1c/Hemoglobin.total in Blood",
                }
            ],
            "text": "Hemoglobin A1c",
        },
        "effectiveDateTime": "2024-03-05T09:30:00-05:00",
        "valueQuantity": {
            "value": 9.4,
            "unit": "%",
            "system": "http://unitsofmeasure.org",
            "code": "%",
        },
    }

    mapped = map_observation_resource(resource)

    assert mapped["fhir_id"] == "131896585"
    assert mapped["code"] == "4548-4"
    assert mapped["display"] == "Hemoglobin A1c/Hemoglobin.total in Blood"
    assert mapped["value"] == "9.4"
    assert mapped["unit"] == "%"
    assert mapped["status"] == "final"
    assert mapped["effective_at"] is not None


def test_map_observation_resource_handles_missing_optional_fields():
    resource = {
        "resourceType": "Observation",
        "id": "observation-1",
    }

    mapped = map_observation_resource(resource)

    assert mapped == {
        "fhir_id": "observation-1",
        "code": None,
        "display": None,
        "value": None,
        "unit": None,
        "status": None,
        "effective_at": None,
    }
