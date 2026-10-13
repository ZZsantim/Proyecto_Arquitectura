from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.service_status.application.use_cases import hash_tracking_code
from app.modules.service_status.domain.entities import PublicServiceStatus
from app.modules.service_status.infrastructure.models import ServiceOrder
from app.modules.technical_record.infrastructure.models import Vehicle


class SqlAlchemyPublicServiceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_by_tracking_code(self, tracking_code: str) -> PublicServiceStatus | None:
        hashed = hash_tracking_code(tracking_code)
        statement = (
            select(ServiceOrder)
            .where(ServiceOrder.tracking_code_hash == hashed)
            .options(selectinload(ServiceOrder.vehicle))
        )
        order = self.session.scalar(statement)
        if order is None:
            return None
        vehicle = order.vehicle
        return PublicServiceStatus(
            status=order.status,
            message=order.status_message,
            vehicle_type=vehicle.vehicle_type,
            serial_number=vehicle.serial_number,
            order_code=order.id,
        )

    def list_orders(self) -> Iterable[ServiceOrder]:
        return self.session.scalars(select(ServiceOrder)).all()
