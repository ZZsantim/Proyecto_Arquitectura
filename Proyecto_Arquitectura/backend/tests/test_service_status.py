from app.modules.service_status.application.use_cases import hash_tracking_code
from app.modules.service_status.infrastructure.models import ServiceOrder


def test_public_status_lookup_returns_minimal_data(client):
    response = client.post(
        "/api/public/service-status",
        json={"tracking_code": "H7-TRACK-001"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "in_review"
    assert payload["message"] == "El vehículo está en revisión técnica."
    assert payload["vehicle_type"] == "bicicleta eléctrica"
    assert payload["serial_number"] == "HU06-EBIKE-0001"
    assert payload["order_code"]


def test_public_status_lookup_rejects_unknown_tracking_code(client):
    response = client.post(
        "/api/public/service-status",
        json={"tracking_code": "NO-EXISTE-999"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "No existe información pública para ese código."


def test_public_status_lookup_respects_rate_limit(client):
    payload = {"tracking_code": "H7-TRACK-001"}
    first = client.post("/api/public/service-status", json=payload)
    second = client.post("/api/public/service-status", json=payload)
    third = client.post("/api/public/service-status", json=payload)
    assert first.status_code == 200
    assert second.status_code == 429
    assert third.status_code == 429


def test_public_status_lookup_rejects_short_code(client):
    response = client.post(
        "/api/public/service-status",
        json={"tracking_code": "ABC"},
    )

    assert response.status_code == 422


def test_tracking_code_hash_is_stable_and_non_plaintext(client):
    hash_value = hash_tracking_code("H7-TRACK-001")
    assert hash_value
    assert "H7-TRACK-001" not in hash_value
    assert client.app.state.test_session.scalar(
        client.app.state.test_session.query(ServiceOrder).filter_by(
            tracking_code_hash=hash_value
        ).statement
    ) is not None
