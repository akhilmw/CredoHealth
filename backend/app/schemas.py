"""API response schemas."""


from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ObservationRead(BaseModel):
    id: int
    fhir_id: str
    code: str | None
    display: str | None
    value: str | None
    unit: str | None
    status: str | None
    effective_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class PatientRead(BaseModel):
    id: int
    fhir_id: str
    given_name: str | None
    family_name: str | None
    gender: str | None
    birth_date: date | None
    source_updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class PatientDetailRead(PatientRead):
    observations: list[ObservationRead] = Field(default_factory=list)


class MigrationResult(BaseModel):
    patients_seen: int
    patients_saved: int
    observations_saved: int
    failures: list[str] = Field(default_factory=list)
