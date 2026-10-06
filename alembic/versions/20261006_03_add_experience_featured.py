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


def upgrade() -> None:
    with op.batch_alter_table("experiences") as batch_op:
        batch_op.add_column(
            sa.Column(
                "featured",
                sa.Boolean(),
                server_default=sa.false(),
                nullable=False,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("experiences") as batch_op:
        batch_op.drop_column("featured")
