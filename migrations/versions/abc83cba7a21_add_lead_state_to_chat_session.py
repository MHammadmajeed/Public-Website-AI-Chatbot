"""add lead state to chat_session

Revision ID: abc83cba7a21
Revises: 74878a053f37
Create Date: 2026-09-21 18:24:23.760129

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'abc83cba7a21'
down_revision: Union[str, Sequence[str], None] = '74878a053f37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chat_session",
        sa.Column("lead_state", sa.String(length=32), server_default="not_started", nullable=False),
    )
    op.add_column(
        "chat_session",
        sa.Column(
            "lead_data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("chat_session", "lead_data")
    op.drop_column("chat_session", "lead_state")