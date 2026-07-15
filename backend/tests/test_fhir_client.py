from app.fhir_client import extract_bundle_resources


def test_extract_bundle_resources_returns_inner_resources():
    bundle = {
        "resourceType": "Bundle",
        "entry": [
            {"resource": {"resourceType": "Patient", "id": "patient-1"}},
            {"resource": {"resourceType": "Patient", "id": "patient-2"}},
        ],
    }

    resources = extract_bundle_resources(bundle, resource_type="Patient")

    assert resources == [
        {"resourceType": "Patient", "id": "patient-1"},
        {"resourceType": "Patient", "id": "patient-2"},
    ]


def test_extract_bundle_resources_ignores_non_matching_resources():
    bundle = {
        "resourceType": "Bundle",
        "entry": [
            {"resource": {"resourceType": "Patient", "id": "patient-1"}},
            {"resource": {"resourceType": "Observation", "id": "observation-1"}},
            {},
        ],
    }

    resources = extract_bundle_resources(bundle, resource_type="Observation")

    assert resources == [{"resourceType": "Observation", "id": "observation-1"}]
