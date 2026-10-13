from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol


@dataclass(frozen=True)
class BatterySpecification:
    voltage: str | None
    amperage: str | None
    capacity: str | None
    cell_type: str | None
    technical_notes: str | None


@dataclass(frozen=True)
class ControllerConfiguration:
    model: str | None
    firmware: str | None
    modifications: str | None


@dataclass(frozen=True)
class Repair:
    id: str
    service_date: date
    summary: str
    technical_details: str | None


@dataclass(frozen=True)
class TechnicalObservation:
    id: str
    content: str
    author_username: str
    created_at: datetime


@dataclass(frozen=True)
class TechnicalRecord:
    id: str
    serial_number: str
    vehicle_type: str
    make_model: str | None
    battery: BatterySpecification | None
    controller: ControllerConfiguration | None
    repairs: list[Repair]
    observations: list[TechnicalObservation]


class TechnicalRecordRepository(Protocol):
    def find_by_serial(self, serial_number: str) -> TechnicalRecord | None: ...

    def update_specifications(
        self,
        *,
        vehicle_id: str,
        battery: BatterySpecification | None,
        controller: ControllerConfiguration | None,
    ) -> TechnicalRecord | None: ...

    def add_observation(
        self, *, vehicle_id: str, author_id: str, content: str
    ) -> TechnicalObservation | None: ...


def normalize_serial_number(serial_number: str) -> str:
    return serial_number.strip().upper()
