"""Add public tracking and service order status to support HU-07."""

import sqlalchemy as sa
from alembic import op

revision = "0003_service_order_public_tracking"
down_revision = "0002_amperage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "service_orders",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("vehicle_id", sa.String(length=36), nullable=False),
        sa.Column("tracking_code_hash", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="received"),
        sa.Column("status_message", sa.String(length=200), nullable=False),
        sa.Column("document_reference", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tracking_code_hash"),
    )
    op.create_index("ix_service_orders_vehicle_id", "service_orders", ["vehicle_id"])


def downgrade() -> None:
    op.drop_index("ix_service_orders_vehicle_id", table_name="service_orders")
    op.drop_table("service_orders")
