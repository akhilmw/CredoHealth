import time
from typing import Any

import httpx

from app.config import settings


def extract_bundle_resources(
    bundle: dict[str, Any],
    resource_type: str | None = None,
) -> list[dict[str, Any]]:
    """Return inner resources from a FHIR search Bundle."""
    resources: list[dict[str, Any]] = []

    for entry in bundle.get("entry", []):
        resource = entry.get("resource") if isinstance(entry, dict) else None
        if not isinstance(resource, dict):
            continue
        if resource_type and resource.get("resourceType") != resource_type:
            continue
        resources.append(resource)

    return resources


class FHIRClientError(Exception):
    """Raised when the external FHIR API cannot return a usable response."""

    pass


class FHIRClient:
    def __init__(
        self,
        base_url: str = settings.fhir_base_url,
        timeout_seconds: float = settings.request_timeout_seconds,
        max_retries: int = settings.max_retries,
        client: httpx.Client | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.client = client or httpx.Client()

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.get(
                    url,
                    params=params,
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if exc.response.status_code < 500 or attempt == self.max_retries:
                    break
                self._sleep_before_retry(attempt)
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = exc
                if attempt == self.max_retries:
                    break
                self._sleep_before_retry(attempt)

        raise FHIRClientError(f"FHIR request failed: {url}") from last_error

    def _sleep_before_retry(self, attempt: int) -> None:
        # Exponential backoff keeps transient HAPI/server issues from turning
        # into tight retry loops.
        time.sleep(0.5 * (2**attempt))

    def fetch_patients(self, limit: int) -> list[dict[str, Any]]:
        bundle = self._get(
            "/Patient",
            params={"_count": limit, "_format": "json"},
        )
        return extract_bundle_resources(bundle, "Patient")

    def fetch_observations_for_patient(
        self,
        patient_fhir_id: str,
    ) -> list[dict[str, Any]]:
        bundle = self._get(
            "/Observation",
            params={
                "subject": f"Patient/{patient_fhir_id}",
                "_format": "json",
            },
        )
        return extract_bundle_resources(bundle, "Observation")
