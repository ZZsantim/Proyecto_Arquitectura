from app.core.security import verify_password
from app.modules.technical_record.infrastructure.models import (
    RepairRecord,
    StaffUser,
    Vehicle,
)
from sqlalchemy import func, select

from scripts.seed_demo import ensure_demo_data, ensure_staff_user


def test_demo_data_loader_is_idempotent(client):
    session = client.app.state.test_session
    ensure_demo_data(session)
    ensure_demo_data(session)

    vehicle_count = session.scalar(select(func.count()).select_from(Vehicle))
    repair_count = session.scalar(select(func.count()).select_from(RepairRecord))
    assert vehicle_count == 3
    assert repair_count == 3


def test_demo_staff_password_is_hashed_and_existing_user_is_preserved(
    client, monkeypatch
):
    session = client.app.state.test_session
    usernames = iter(["demo_mechanic", "demo_mechanic"])
    passwords = iter(["Synthetic-only-password-2026", "Synthetic-only-password-2026"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(usernames))
    monkeypatch.setattr("scripts.seed_demo.getpass", lambda _prompt: next(passwords))

    ensure_staff_user(session)
    user = session.scalar(
        select(StaffUser).where(StaffUser.username == "demo_mechanic")
    )
    assert user is not None
    assert user.password_hash != "Synthetic-only-password-2026"
    assert verify_password("Synthetic-only-password-2026", user.password_hash)
    original_hash = user.password_hash

    ensure_staff_user(session)

    assert user.password_hash == original_hash
