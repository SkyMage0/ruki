"""Add workers_needed field to tasks.

Revision ID: 003
Revises: 002
Create Date: 2025-03-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column("workers_needed", sa.Integer(), nullable=False, server_default="1"),
    )
    op.alter_column("tasks", "workers_needed", server_default=None)


def downgrade() -> None:
    op.drop_column("tasks", "workers_needed")

