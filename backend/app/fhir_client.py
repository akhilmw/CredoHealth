"""FHIR API client helpers.

The HAPI search endpoints return FHIR Bundles. The migration maps the inner
resources from each Bundle entry, not the Bundle itself.
"""

from typing import Any


def extract_bundle_resources(
    bundle: dict[str, Any],
    resource_type: str | None = None,
) -> list[dict[str, Any]]:
    resources: list[dict[str, Any]] = []

    for entry in bundle.get("entry", []):
        resource = entry.get("resource") if isinstance(entry, dict) else None
        if not isinstance(resource, dict):
            continue
        if resource_type and resource.get("resourceType") != resource_type:
            continue
        resources.append(resource)

    return resources
