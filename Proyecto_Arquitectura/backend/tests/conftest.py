import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault(
    "JWT_SECRET_KEY", "pytest-only-secret-with-more-than-32-characters"
)
os.environ.setdefault("FRONTEND_DIR", "frontend")

import pytest
from app.core.database import Base, get_db
from app.core.rate_limit import public_lookup_limiter
from app.core.security import hash_password
from app.main import app
from app.modules.service_status.application.use_cases import create_service_order
from app.modules.service_status.infrastructure.models import ServiceOrder
from app.modules.technical_record.infrastructure.models import (
    BatterySpecification,
    ControllerConfiguration,
    RepairRecord,
    StaffUser,
    Vehicle,
)
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture()
def client():
    test_engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(
        test_engine,
        "connect",
        lambda connection, _record: connection.execute("PRAGMA foreign_keys=ON"),
    )
    TestingSession = sessionmaker(
        bind=test_engine, autoflush=False, expire_on_commit=False
    )
    Base.metadata.create_all(test_engine)
    session = TestingSession()
    mechanic = StaffUser(
        id="staff-mechanic",
        username="mecanico",
        password_hash=hash_password("prueba-segura"),
        role="mechanic",
    )
    viewer = StaffUser(
        id="staff-viewer",
        username="lector",
        password_hash=hash_password("prueba-segura"),
        role="viewer",
    )
    vehicle = Vehicle(
        id="vehicle-1",
        serial_number="HU06-EBIKE-0001",
        vehicle_type="bicicleta eléctrica",
        make_model="Modelo sintético A",
        battery=BatterySpecification(
            id="battery-1",
            voltage="48 V (dato sintético)",
            amperage="20 A (dato sintético)",
            capacity="15 Ah (dato sintético)",
            cell_type="Li-ion (dato sintético)",
            technical_notes="Configuración de demostración",
        ),
        controller=ControllerConfiguration(
            id="controller-1",
            model="Controlador demo",
            firmware="1.0-demo",
            modifications="Ajuste sintético",
        ),
        repairs=[
            RepairRecord(
                id="repair-1",
                service_date=__import__("datetime").date(2025, 2, 3),
                summary="Revisión sintética",
                technical_details="Inspección de conectores.",
            )
        ],
    )
    session.add_all([mechanic, viewer, vehicle])
    session.commit()
    create_service_order(
        session,
        vehicle=vehicle,
        tracking_code="H7-TRACK-001",
        status="in_review",
        status_message="El vehículo está en revisión técnica.",
    )

    def override_get_db():
        request_session = TestingSession()
        try:
            yield request_session
        finally:
            request_session.close()

    public_lookup_limiter.reset()
    app.dependency_overrides[get_db] = override_get_db
    app.state.test_session = session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    del app.state.test_session
    session.close()
    Base.metadata.drop_all(test_engine)
    test_engine.dispose()


@pytest.fixture()
def mechanic_token(client):
    response = client.post(
        "/api/v1/auth/token",
        json={"username": "mecanico", "password": "prueba-segura"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]
