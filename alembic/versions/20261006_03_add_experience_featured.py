"""add featured flag to experiences

Revision ID: 20261006_03
Revises: 20260917_02
Create Date: 2026-10-06 11:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20261006_03"
down_revision: str | Sequence[str] | None = "20260917_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Batch mode would rebuild the table by dropping the old one, and with foreign
# keys on, that drop cascades to experience_accomplishments and
# experience_skills. A plain ADD COLUMN changes the table in place.
def upgrade() -> None:
    op.add_column(
        "experiences",
        sa.Column(
            "featured",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.execute("ALTER TABLE experiences DROP COLUMN featured")
