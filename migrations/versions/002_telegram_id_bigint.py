"""Change users.telegram_id to BIGINT (Telegram IDs can exceed int32).

Revision ID: 002
Revises: 001
Create Date: 2025-03-13

"""
from collections.abc import Sequence

from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ALTER COLUMN telegram_id TYPE BIGINT USING telegram_id::BIGINT")


def downgrade() -> None:
    op.execute("ALTER TABLE users ALTER COLUMN telegram_id TYPE INTEGER USING telegram_id::INTEGER")
