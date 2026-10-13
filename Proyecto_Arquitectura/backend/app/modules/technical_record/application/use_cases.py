from app.modules.technical_record.domain.entities import (
    BatterySpecification,
    ControllerConfiguration,
    TechnicalObservation,
    TechnicalRecord,
    TechnicalRecordRepository,
    normalize_serial_number,
)


def find_technical_record(
    repository: TechnicalRecordRepository, serial_number: str
) -> TechnicalRecord | None:
    return repository.find_by_serial(normalize_serial_number(serial_number))


def add_technical_observation(
    repository: TechnicalRecordRepository,
    *,
    vehicle_id: str,
    author_id: str,
    content: str,
) -> TechnicalObservation | None:
    normalized_content = content.strip()
    if not normalized_content:
        raise ValueError("La observación no puede estar vacía.")
    return repository.add_observation(
        vehicle_id=vehicle_id,
        author_id=author_id,
        content=normalized_content,
    )


def update_technical_specifications(
    repository: TechnicalRecordRepository,
    *,
    vehicle_id: str,
    battery: BatterySpecification | None,
    controller: ControllerConfiguration | None,
) -> TechnicalRecord | None:
    return repository.update_specifications(
        vehicle_id=vehicle_id,
        battery=battery,
        controller=controller,
    )
