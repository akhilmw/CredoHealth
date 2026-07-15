from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)
    fhir_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    given_name: Mapped[str | None] = mapped_column(String(255))
    family_name: Mapped[str | None] = mapped_column(String(255))
    gender: Mapped[str | None] = mapped_column(String(64))
    birth_date: Mapped[date | None] = mapped_column(Date)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime)

    observations: Mapped[list["Observation"]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
    )


class Observation(Base):
    __tablename__ = "observations"
    __table_args__ = (UniqueConstraint("patient_id", "fhir_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    fhir_id: Mapped[str] = mapped_column(String(128), index=True)
    code: Mapped[str | None] = mapped_column(String(128))
    display: Mapped[str | None] = mapped_column(String(255))
    value: Mapped[str | None] = mapped_column(Text)
    unit: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str | None] = mapped_column(String(64))
    effective_at: Mapped[datetime | None] = mapped_column(DateTime)

    patient: Mapped[Patient] = relationship(back_populates="observations")
