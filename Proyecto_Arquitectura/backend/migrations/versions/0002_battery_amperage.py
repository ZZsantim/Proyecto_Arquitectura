"""Add descriptive battery amperage to the HU-06 record."""

import sqlalchemy as sa
from alembic import op

revision = "0002_amperage"
down_revision = "0001_hu06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "battery_specifications",
        sa.Column("amperage", sa.String(length=80), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("battery_specifications", "amperage")
