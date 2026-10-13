from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def new_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class StaffUser(Base):
    __tablename__ = "staff_users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30))
    is_active: Mapped[bool] = mapped_column(default=True)


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    serial_number: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    vehicle_type: Mapped[str] = mapped_column(String(40), nullable=False)
    make_model: Mapped[str | None] = mapped_column(String(120))

    battery: Mapped["BatterySpecification | None"] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan", uselist=False
    )
    controller: Mapped["ControllerConfiguration | None"] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan", uselist=False
    )
    repairs: Mapped[list["RepairRecord"]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan"
    )
    observations: Mapped[list["TechnicalObservation"]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan"
    )


class BatterySpecification(Base):
    __tablename__ = "battery_specifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    vehicle_id: Mapped[str] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    voltage: Mapped[str | None] = mapped_column(String(80))
    amperage: Mapped[str | None] = mapped_column(String(80))
    capacity: Mapped[str | None] = mapped_column(String(80))
    cell_type: Mapped[str | None] = mapped_column(String(120))
    technical_notes: Mapped[str | None] = mapped_column(Text)
    vehicle: Mapped[Vehicle] = relationship(back_populates="battery")


class ControllerConfiguration(Base):
    __tablename__ = "controller_configurations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    vehicle_id: Mapped[str] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    model: Mapped[str | None] = mapped_column(String(120))
    firmware: Mapped[str | None] = mapped_column(String(120))
    modifications: Mapped[str | None] = mapped_column(Text)
    vehicle: Mapped[Vehicle] = relationship(back_populates="controller")


class RepairRecord(Base):
    __tablename__ = "repair_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    vehicle_id: Mapped[str] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    service_date: Mapped[date] = mapped_column(Date, nullable=False)
    summary: Mapped[str] = mapped_column(String(240), nullable=False)
    technical_details: Mapped[str | None] = mapped_column(Text)
    vehicle: Mapped[Vehicle] = relationship(back_populates="repairs")


class TechnicalObservation(Base):
    __tablename__ = "technical_observations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    vehicle_id: Mapped[str] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    author_id: Mapped[str] = mapped_column(
        ForeignKey("staff_users.id", ondelete="RESTRICT"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    vehicle: Mapped[Vehicle] = relationship(back_populates="observations")
    author: Mapped[StaffUser] = relationship()
