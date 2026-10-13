import os

from alembic import command
from alembic.config import Config
from app.core.config import get_settings
from sqlalchemy import create_engine, inspect


def test_migration_builds_schema_and_serial_index_from_empty_database(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'migration.db'}"
    previous_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    get_settings.cache_clear()
    try:
        alembic_config = Config("backend/alembic.ini")
        command.upgrade(alembic_config, "head")
    finally:
        if previous_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_url
        get_settings.cache_clear()

    engine = create_engine(database_url)
    inspector = inspect(engine)
    assert {
        "staff_users",
        "vehicles",
        "battery_specifications",
        "controller_configurations",
        "repair_records",
        "technical_observations",
    }.issubset(set(inspector.get_table_names()))
    serial_indexes = inspector.get_indexes("vehicles")
    assert any(
        index["name"] == "ix_vehicles_serial_number" and index["unique"]
        for index in serial_indexes
    )
    engine.dispose()
