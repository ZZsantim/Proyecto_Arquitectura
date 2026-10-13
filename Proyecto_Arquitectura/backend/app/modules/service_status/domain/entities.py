from dataclasses import dataclass


@dataclass(frozen=True)
class PublicServiceStatus:
    status: str
    message: str
    vehicle_type: str | None = None
    serial_number: str | None = None
    order_code: str | None = None


@dataclass(frozen=True)
class ServiceOrder:
    id: str
    vehicle_id: str
    tracking_code: str
    status: str
    status_message: str
    document_reference: str | None = None


@dataclass(frozen=True)
class PublicLookupResult:
    tracked: bool
    status: str
    message: str
