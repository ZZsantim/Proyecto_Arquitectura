import os
import sys
import tempfile
from datetime import date
from statistics import median
from time import perf_counter
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault(
    "JWT_SECRET_KEY", "benchmark-only-secret-with-at-least-32-characters"
)

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, selectinload

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.database import Base  # noqa: E402
from app.modules.technical_record.infrastructure.models import (  # noqa: E402
    RepairRecord,
    Vehicle,
)

VEHICLE_COUNT = 5_000
REPAIR_COUNT = 50_000
SEARCH_SERIAL = "BENCH-SERIAL-004999"


def seed_benchmark(session: Session) -> str:
    vehicles = [
        Vehicle(
            id=str(uuid4()),
            serial_number=f"BENCH-SERIAL-{index:06d}",
            vehicle_type="bicicleta eléctrica",
            make_model="Modelo sintético de rendimiento",
        )
        for index in range(VEHICLE_COUNT)
    ]
    session.add_all(vehicles)
    session.flush()
    repairs = [
        RepairRecord(
            id=str(uuid4()),
            vehicle_id=vehicles[index % VEHICLE_COUNT].id,
            service_date=date(2025, 1, (index % 28) + 1),
            summary=f"Reparación sintética {index}",
        )
        for index in range(REPAIR_COUNT)
    ]
    session.add_all(repairs)
    session.commit()
    return vehicles[-1].id


def query_record(session: Session) -> Vehicle | None:
    return session.scalar(
        select(Vehicle)
        .where(Vehicle.serial_number == SEARCH_SERIAL)
        .options(selectinload(Vehicle.repairs))
    )


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="hu06-benchmark-") as directory:
        engine = create_engine(f"sqlite+pysqlite:///{directory}/benchmark.db")
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            target_id = seed_benchmark(session)
        timings = []
        record = None
        for _ in range(20):
            with Session(engine) as query_session:
                started = perf_counter()
                record = query_record(query_session)
                timings.append(perf_counter() - started)
        if record is None or record.id != target_id:
            raise RuntimeError("La búsqueda indexada no devolvió el vehículo esperado.")
        elapsed_ms = [value * 1000 for value in timings]
        p50 = median(elapsed_ms)
        p95 = sorted(elapsed_ms)[int(len(elapsed_ms) * 0.95) - 1]
        print(
            f"Motor=SQLite; vehículos={VEHICLE_COUNT}; "
            f"reparaciones={REPAIR_COUNT}; "
            f"reparaciones_encontradas={len(record.repairs)}; "
            f"mediana_ms={p50:.3f}; p95_ms={p95:.3f}; "
            f"meta_menor_2000_ms={'cumplida' if p95 < 2000 else 'no cumplida'}"
        )
        engine.dispose()


if __name__ == "__main__":
    main()
