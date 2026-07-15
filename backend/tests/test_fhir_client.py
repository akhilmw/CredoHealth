import httpx
import pytest

from app.fhir_client import FHIRClient, FHIRClientError, extract_bundle_resources


# Verifies that FHIR Bundle entries are flattened into raw resources.
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


# Verifies that optional resource type filtering ignores unrelated entries.
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


# Verifies that fetch_patients returns only Patient resources from the Bundle.
def test_fetch_patients_returns_inner_patient_resources():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/Patient"
        assert request.url.params["_count"] == "2"
        return httpx.Response(
            200,
            json={
                "resourceType": "Bundle",
                "entry": [
                    {"resource": {"resourceType": "Patient", "id": "patient-1"}},
                    {"resource": {"resourceType": "Observation", "id": "ignored"}},
                ],
            },
        )

    client = FHIRClient(
        base_url="https://example.test",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    patients = client.fetch_patients(limit=2)

    assert patients == [{"resourceType": "Patient", "id": "patient-1"}]


# Verifies that transient server errors are retried before succeeding.
def test_get_retries_5xx_then_returns_json():
    responses = iter(
        [
            httpx.Response(503, json={"error": "try later"}),
            httpx.Response(200, json={"resourceType": "Bundle", "entry": []}),
        ]
    )

    client = FHIRClient(
        base_url="https://example.test",
        client=httpx.Client(
            transport=httpx.MockTransport(lambda request: next(responses))
        ),
    )
    client._sleep_before_retry = lambda attempt: None

    assert client._get("/Patient", params={}) == {
        "resourceType": "Bundle",
        "entry": [],
    }


# Verifies that repeated network failures become a domain-specific client error.
def test_get_raises_client_error_after_repeated_network_failures():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection failed", request=request)

    client = FHIRClient(
        base_url="https://example.test",
        max_retries=1,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    client._sleep_before_retry = lambda attempt: None

    with pytest.raises(FHIRClientError):
        client._get("/Patient", params={})
