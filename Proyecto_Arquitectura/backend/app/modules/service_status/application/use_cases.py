import hashlib

from app.modules.service_status.domain.entities import PublicServiceStatus
from app.modules.service_status.infrastructure.models import ServiceOrder
from app.modules.technical_record.infrastructure.models import Vehicle


def normalize_tracking_code(value: str) -> str:
    return value.strip().upper()


def hash_tracking_code(value: str) -> str:
    return hashlib.sha256(value.strip().upper().encode("utf-8")).hexdigest()


def lookup_public_status(repository, tracking_code: str) -> PublicServiceStatus | None:
    code = normalize_tracking_code(tracking_code)
    if not code or len(code) > 32:
        raise ValueError("El código de seguimiento debe tener entre 1 y 32 caracteres.")
    return repository.find_by_tracking_code(code)


def create_service_order(
    session,
    *,
    vehicle: Vehicle,
    tracking_code: str,
    status: str,
    status_message: str,
    document_reference: str | None = None,
) -> ServiceOrder:
    order = ServiceOrder(
        vehicle_id=vehicle.id,
        tracking_code_hash=hash_tracking_code(tracking_code),
        status=status,
        status_message=status_message,
        document_reference=document_reference,
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    return order
