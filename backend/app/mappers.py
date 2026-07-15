"""FHIR-to-internal transformation helpers."""

from datetime import date, datetime
from typing import Any


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _first(items: list[Any] | None) -> Any | None:
    if not items:
        return None
    return items[0]


def map_patient_resource(resource: dict[str, Any]) -> dict[str, Any]:
    name = _first(resource.get("name"))
    given_names = name.get("given") if isinstance(name, dict) else None

    return {
        "fhir_id": resource["id"],
        "given_name": _first(given_names),
        "family_name": name.get("family") if isinstance(name, dict) else None,
        "gender": resource.get("gender"),
        "birth_date": _parse_date(resource.get("birthDate")),
        "source_updated_at": _parse_datetime(resource.get("meta", {}).get("lastUpdated")),
    }


def map_observation_resource(resource: dict[str, Any]) -> dict[str, Any]:
    coding = _first(resource.get("code", {}).get("coding"))
    value, unit = _map_observation_value(resource)

    return {
        "fhir_id": resource["id"],
        "code": coding.get("code") if isinstance(coding, dict) else None,
        "display": coding.get("display") if isinstance(coding, dict) else None,
        "value": value,
        "unit": unit,
        "status": resource.get("status"),
        "effective_at": _parse_datetime(resource.get("effectiveDateTime")),
    }


def _map_observation_value(resource: dict[str, Any]) -> tuple[str | None, str | None]:
    quantity = resource.get("valueQuantity")
    if isinstance(quantity, dict):
        raw_value = quantity.get("value")
        return (
            str(raw_value) if raw_value is not None else None,
            quantity.get("unit") or quantity.get("code"),
        )

    for key in ("valueString", "valueCode", "valueBoolean", "valueInteger"):
        if key in resource:
            return str(resource[key]), None

    concept = resource.get("valueCodeableConcept")
    if isinstance(concept, dict):
        coding = _first(concept.get("coding"))
        if isinstance(coding, dict):
            return coding.get("display") or coding.get("code"), None
        return concept.get("text"), None

    return None, None
