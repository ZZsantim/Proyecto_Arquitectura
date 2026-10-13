import os
import sys
from datetime import date
from getpass import getpass

from sqlalchemy import select
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.database import SessionLocal  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.modules.technical_record.infrastructure.models import (  # noqa: E402
    BatterySpecification,
    ControllerConfiguration,
    RepairRecord,
    StaffUser,
    Vehicle,
)

DEMO_VEHICLES = (
    {
        "serial_number": "HU06-EBIKE-0001",
        "vehicle_type": "bicicleta eléctrica",
        "make_model": "Modelo sintético A",
        "battery": {
            "voltage": "48 V (dato sintético)",
            "amperage": "20 A (dato sintético)",
            "capacity": "15 Ah (dato sintético)",
            "cell_type": "Li-ion (dato sintético)",
            "technical_notes": "Configuración de demostración",
        },
        "controller": {
            "model": "Controlador demo A",
            "firmware": "1.0-demo",
            "modifications": "Configuración original sintética",
        },
    },
    {
        "serial_number": "HU06-SCOOTER-0002",
        "vehicle_type": "patineta eléctrica",
        "make_model": "Modelo sintético B",
        "battery": None,
        "controller": {
            "model": "Controlador demo B",
            "firmware": None,
            "modifications": "Limitación de velocidad revisada (dato sintético)",
        },
    },
    {
        "serial_number": "HU06-EBIKE-0003",
        "vehicle_type": "bicicleta eléctrica",
        "make_model": "Modelo sintético C",
        "battery": {
            "voltage": "36 V (dato sintético)",
            "amperage": None,
            "capacity": None,
            "cell_type": "Li-ion (dato sintético)",
            "technical_notes": None,
        },
        "controller": None,
    },
)

DEMO_REPAIRS = (
    (
        "HU06-EBIKE-0001",
        "2025-02-03",
        "Revisión del sistema eléctrico",
        "Inspección y ajuste de conectores (dato sintético).",
    ),
    (
        "HU06-EBIKE-0001",
        "2025-04-18",
        "Mantenimiento preventivo",
        "Revisión de cableado y fijaciones (dato sintético).",
    ),
)


def ensure_demo_data(session: Session) -> None:
    vehicles_by_serial: dict[str, Vehicle] = {}
    for item in DEMO_VEHICLES:
        vehicle = session.scalar(
            select(Vehicle).where(Vehicle.serial_number == item["serial_number"])
        )
        if vehicle is None:
            vehicle = Vehicle(
                serial_number=item["serial_number"],
                vehicle_type=item["vehicle_type"],
                make_model=item["make_model"],
            )
            session.add(vehicle)
            session.flush()
        vehicles_by_serial[vehicle.serial_number] = vehicle

        if item["battery"] and vehicle.battery is None:
            vehicle.battery = BatterySpecification(**item["battery"])
        if item["controller"] and vehicle.controller is None:
            vehicle.controller = ControllerConfiguration(**item["controller"])

    session.flush()
    for serial_number, date_value, summary, details in DEMO_REPAIRS:
        vehicle = vehicles_by_serial[serial_number]
        already_exists = session.scalar(
            select(RepairRecord.id).where(
                RepairRecord.vehicle_id == vehicle.id,
                RepairRecord.summary == summary,
            )
        )
        if already_exists is None:
            session.add(
                RepairRecord(
                    vehicle_id=vehicle.id,
                    service_date=date.fromisoformat(date_value),
                    summary=summary,
                    technical_details=details,
                )
            )
    session.commit()


def ensure_staff_user(session: Session) -> None:
    username = input("Usuario de taller para la demostración: ").strip()
    if not username or len(username) > 80:
        raise ValueError("El usuario debe tener entre 1 y 80 caracteres.")
    user = session.scalar(select(StaffUser).where(StaffUser.username == username))
    if user is not None:
        print("El usuario ya existe; no se modificó.")
        return

    password = getpass("Contraseña (mínimo 12 caracteres): ")
    confirmation = getpass("Repita la contraseña: ")
    if len(password) < 12 or password != confirmation:
        raise ValueError(
            "Las contraseñas deben coincidir y tener al menos 12 caracteres."
        )
    session.add(
        StaffUser(
            username=username,
            password_hash=hash_password(password),
            role="mechanic",
            is_active=True,
        )
    )
    session.commit()
    print("Usuario de demostración creado con hash Argon2id.")


def main() -> None:
    with SessionLocal() as session:
        ensure_demo_data(session)
        ensure_staff_user(session)
    print("Datos ficticios cargados de forma idempotente.")


if __name__ == "__main__":
    main()
