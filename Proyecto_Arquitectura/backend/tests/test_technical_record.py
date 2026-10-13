from datetime import date

import pytest
from app.modules.technical_record.infrastructure.models import RepairRecord, Vehicle
from sqlalchemy.exc import IntegrityError


def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_login_issues_expiring_bearer_token(client):
    response = client.post(
        "/api/v1/auth/token",
        json={"username": "mecanico", "password": "prueba-segura"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["expires_in"] == 1800


def test_login_rejects_invalid_password(client):
    response = client.post(
        "/api/v1/auth/token",
        json={"username": "mecanico", "password": "incorrecta"},
    )

    assert response.status_code == 401


def test_search_returns_vehicle_specs_and_repair_history(client, mechanic_token):
    response = client.get(
        "/api/v1/technical-records/by-serial/hu06-ebike-0001",
        headers=authorization(mechanic_token),
    )

    assert response.status_code == 200
    record = response.json()
    assert record["serial_number"] == "HU06-EBIKE-0001"
    assert record["battery"]["voltage"] == "48 V (dato sintético)"
    assert record["battery"]["amperage"] == "20 A (dato sintético)"
    assert record["controller"]["modifications"] == "Ajuste sintético"
    assert len(record["repairs"]) == 1
    assert record["repairs"][0]["summary"] == "Revisión sintética"
    assert response.headers["cache-control"] == "no-store"


def test_search_returns_empty_history_when_vehicle_has_no_repairs(
    client, mechanic_token
):
    session = client.app.state.test_session
    session.add(
        Vehicle(
            id="vehicle-without-repairs",
            serial_number="HU06-EBIKE-EMPTY",
            vehicle_type="patineta eléctrica",
            make_model="Modelo sintético vacío",
        )
    )
    session.commit()
    response = client.get(
        "/api/v1/technical-records/by-serial/HU06-EBIKE-EMPTY",
        headers=authorization(mechanic_token),
    )

    assert response.status_code == 200
    assert response.json()["repairs"] == []


def test_missing_vehicle_returns_clear_message(client, mechanic_token):
    response = client.get(
        "/api/v1/technical-records/by-serial/UNKNOWN",
        headers=authorization(mechanic_token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Vehículo no encontrado."


def test_search_requires_authentication(client):
    response = client.get("/api/v1/technical-records/by-serial/HU06-EBIKE-0001")

    assert response.status_code == 401


def test_user_without_staff_role_is_forbidden(client):
    token = client.post(
        "/api/v1/auth/token",
        json={"username": "lector", "password": "prueba-segura"},
    ).json()["access_token"]

    response = client.get(
        "/api/v1/technical-records/by-serial/HU06-EBIKE-0001",
        headers=authorization(token),
    )

    assert response.status_code == 403


def test_observation_is_persisted_as_inert_plain_text(client, mechanic_token):
    record = client.get(
        "/api/v1/technical-records/by-serial/HU06-EBIKE-0001",
        headers=authorization(mechanic_token),
    ).json()
    payload = "<script>alert('xss')</script> Revisar cable"
    response = client.post(
        f"/api/v1/technical-records/{record['id']}/observations",
        headers=authorization(mechanic_token),
        json={"content": payload},
    )

    assert response.status_code == 201
    assert response.json()["content"] == payload
    read_back = client.get(
        "/api/v1/technical-records/by-serial/HU06-EBIKE-0001",
        headers=authorization(mechanic_token),
    ).json()
    assert read_back["observations"][0]["content"] == payload


def test_blank_observation_is_rejected(client, mechanic_token):
    response = client.post(
        "/api/v1/technical-records/vehicle-1/observations",
        headers=authorization(mechanic_token),
        json={"content": "   "},
    )

    assert response.status_code == 422


def test_observation_for_missing_vehicle_is_not_created(client, mechanic_token):
    response = client.post(
        "/api/v1/technical-records/missing/observations",
        headers=authorization(mechanic_token),
        json={"content": "Observación sintética"},
    )

    assert response.status_code == 404


def test_observation_write_requires_staff_authentication(client):
    response = client.post(
        "/api/v1/technical-records/vehicle-1/observations",
        json={"content": "Observación sin autenticar"},
    )

    assert response.status_code == 401


def test_authorized_staff_can_register_technical_specifications(client, mechanic_token):
    response = client.put(
        "/api/v1/technical-records/vehicle-1/specifications",
        headers=authorization(mechanic_token),
        json={
            "battery": {
                "voltage": "52 V sintético",
                "amperage": "22 A sintético",
                "capacity": "18 Ah sintético",
                "cell_type": "Li-ion sintético",
                "technical_notes": "Configuración registrada por prueba.",
            },
            "controller": {
                "model": "Controlador actualizado",
                "firmware": "2.0",
                "modifications": "Ajuste registrado por prueba.",
            },
        },
    )

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["battery"]["amperage"] == "22 A sintético"
    assert response.json()["controller"]["model"] == "Controlador actualizado"


def test_user_without_staff_role_cannot_modify_specifications(client):
    token = client.post(
        "/api/v1/auth/token",
        json={"username": "lector", "password": "prueba-segura"},
    ).json()["access_token"]
    response = client.put(
        "/api/v1/technical-records/vehicle-1/specifications",
        headers=authorization(token),
        json={"battery": None, "controller": None},
    )

    assert response.status_code == 403


def test_specification_fields_enforce_length_limits(client, mechanic_token):
    response = client.put(
        "/api/v1/technical-records/vehicle-1/specifications",
        headers=authorization(mechanic_token),
        json={
            "battery": {"voltage": "V" * 81},
            "controller": None,
        },
    )

    assert response.status_code == 422


def test_repairs_are_returned_most_recent_first(client, mechanic_token):
    session = client.app.state.test_session
    session.add(
        RepairRecord(
            id="repair-2",
            vehicle_id="vehicle-1",
            service_date=date(2025, 4, 3),
            summary="Segunda revisión sintética",
        )
    )
    session.commit()

    response = client.get(
        "/api/v1/technical-records/by-serial/HU06-EBIKE-0001",
        headers=authorization(mechanic_token),
    )

    assert [item["summary"] for item in response.json()["repairs"]] == [
        "Segunda revisión sintética",
        "Revisión sintética",
    ]


def test_duplicate_serial_number_is_rejected_by_database(client):
    session = client.app.state.test_session
    session.add(
        Vehicle(
            id="vehicle-duplicate",
            serial_number="HU06-EBIKE-0001",
            vehicle_type="bicicleta eléctrica",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_frontend_is_served_by_the_application(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "Expediente técnico" in response.text
