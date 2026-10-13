"""Create the HU-06 technical record tables."""

import sqlalchemy as sa
from alembic import op

revision = "0001_hu06"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "staff_users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_staff_users_username", "staff_users", ["username"], unique=True)
    op.create_table(
        "vehicles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("serial_number", sa.String(length=64), nullable=False),
        sa.Column("vehicle_type", sa.String(length=40), nullable=False),
        sa.Column("make_model", sa.String(length=120), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_vehicles_serial_number", "vehicles", ["serial_number"], unique=True
    )
    op.create_table(
        "battery_specifications",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("vehicle_id", sa.String(length=36), nullable=False),
        sa.Column("voltage", sa.String(length=80), nullable=True),
        sa.Column("capacity", sa.String(length=80), nullable=True),
        sa.Column("cell_type", sa.String(length=120), nullable=True),
        sa.Column("technical_notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vehicle_id"),
    )
    op.create_table(
        "controller_configurations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("vehicle_id", sa.String(length=36), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=True),
        sa.Column("firmware", sa.String(length=120), nullable=True),
        sa.Column("modifications", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vehicle_id"),
    )
    op.create_table(
        "repair_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("vehicle_id", sa.String(length=36), nullable=False),
        sa.Column("service_date", sa.Date(), nullable=False),
        sa.Column("summary", sa.String(length=240), nullable=False),
        sa.Column("technical_details", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_repair_records_vehicle_id", "repair_records", ["vehicle_id"])
    op.create_table(
        "technical_observations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("vehicle_id", sa.String(length=36), nullable=False),
        sa.Column("author_id", sa.String(length=36), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["staff_users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_technical_observations_vehicle_id",
        "technical_observations",
        ["vehicle_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_technical_observations_vehicle_id", table_name="technical_observations"
    )
    op.drop_table("technical_observations")
    op.drop_index("ix_repair_records_vehicle_id", table_name="repair_records")
    op.drop_table("repair_records")
    op.drop_table("controller_configurations")
    op.drop_table("battery_specifications")
    op.drop_index("ix_vehicles_serial_number", table_name="vehicles")
    op.drop_table("vehicles")
    op.drop_index("ix_staff_users_username", table_name="staff_users")
    op.drop_table("staff_users")
