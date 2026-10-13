from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.technical_record.domain.entities import (
    BatterySpecification as BatteryEntity,
)
from app.modules.technical_record.domain.entities import (
    ControllerConfiguration as ControllerEntity,
)
from app.modules.technical_record.domain.entities import (
    Repair,
    TechnicalRecord,
)
from app.modules.technical_record.domain.entities import (
    TechnicalObservation as ObservationEntity,
)
from app.modules.technical_record.infrastructure.models import (
    BatterySpecification,
    ControllerConfiguration,
    TechnicalObservation,
    Vehicle,
)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class SqlAlchemyTechnicalRecordRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_by_serial(self, serial_number: str) -> TechnicalRecord | None:
        statement = (
            select(Vehicle)
            .where(Vehicle.serial_number == serial_number)
            .options(
                selectinload(Vehicle.battery),
                selectinload(Vehicle.controller),
                selectinload(Vehicle.repairs),
                selectinload(Vehicle.observations).selectinload(
                    TechnicalObservation.author
                ),
            )
        )
        vehicle = self.session.scalar(statement)
        if vehicle is None:
            return None

        repairs = [
            Repair(
                id=item.id,
                service_date=item.service_date,
                summary=item.summary,
                technical_details=item.technical_details,
            )
            for item in sorted(
                vehicle.repairs,
                key=lambda item: (item.service_date, item.id),
                reverse=True,
            )
        ]
        observations = [
            ObservationEntity(
                id=item.id,
                content=item.content,
                author_username=item.author.username,
                created_at=as_utc(item.created_at),
            )
            for item in sorted(
                vehicle.observations,
                key=lambda item: (item.created_at, item.id),
                reverse=True,
            )
        ]
        battery = (
            BatteryEntity(
                voltage=vehicle.battery.voltage,
                amperage=vehicle.battery.amperage,
                capacity=vehicle.battery.capacity,
                cell_type=vehicle.battery.cell_type,
                technical_notes=vehicle.battery.technical_notes,
            )
            if vehicle.battery
            else None
        )
        controller = (
            ControllerEntity(
                model=vehicle.controller.model,
                firmware=vehicle.controller.firmware,
                modifications=vehicle.controller.modifications,
            )
            if vehicle.controller
            else None
        )
        return TechnicalRecord(
            id=vehicle.id,
            serial_number=vehicle.serial_number,
            vehicle_type=vehicle.vehicle_type,
            make_model=vehicle.make_model,
            battery=battery,
            controller=controller,
            repairs=repairs,
            observations=observations,
        )

    def add_observation(
        self, *, vehicle_id: str, author_id: str, content: str
    ) -> ObservationEntity | None:
        vehicle = self.session.get(Vehicle, vehicle_id)
        if vehicle is None:
            return None
        observation = TechnicalObservation(
            vehicle_id=vehicle_id, author_id=author_id, content=content
        )
        self.session.add(observation)
        self.session.commit()
        self.session.refresh(observation)
        return ObservationEntity(
            id=observation.id,
            content=observation.content,
            author_username=observation.author.username,
            created_at=as_utc(observation.created_at),
        )

    def update_specifications(
        self,
        *,
        vehicle_id: str,
        battery: BatteryEntity | None,
        controller: ControllerEntity | None,
    ) -> TechnicalRecord | None:
        vehicle = self.session.get(Vehicle, vehicle_id)
        if vehicle is None:
            return None

        if battery is None:
            vehicle.battery = None
        elif vehicle.battery is None:
            vehicle.battery = BatterySpecification(
                vehicle_id=vehicle_id,
                voltage=battery.voltage,
                amperage=battery.amperage,
                capacity=battery.capacity,
                cell_type=battery.cell_type,
                technical_notes=battery.technical_notes,
            )
        else:
            vehicle.battery.voltage = battery.voltage
            vehicle.battery.amperage = battery.amperage
            vehicle.battery.capacity = battery.capacity
            vehicle.battery.cell_type = battery.cell_type
            vehicle.battery.technical_notes = battery.technical_notes

        if controller is None:
            vehicle.controller = None
        elif vehicle.controller is None:
            vehicle.controller = ControllerConfiguration(
                vehicle_id=vehicle_id,
                model=controller.model,
                firmware=controller.firmware,
                modifications=controller.modifications,
            )
        else:
            vehicle.controller.model = controller.model
            vehicle.controller.firmware = controller.firmware
            vehicle.controller.modifications = controller.modifications

        self.session.commit()
        return self.find_by_serial(vehicle.serial_number)
