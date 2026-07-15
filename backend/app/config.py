from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    fhir_base_url: str = "https://hapi.fhir.org/baseR4"
    database_url: str = "sqlite:///./credo_health.db"
    request_timeout_seconds: float = Field(default=15.0, gt=0)
    max_retries: int = Field(default=3, ge=0)


settings = Settings()
