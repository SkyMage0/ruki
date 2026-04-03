"""Initial schema: cities, users, tasks, bids, reviews, verification_requests.

Revision ID: 001
Revises:
Create Date: 2025-03-13

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cities",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("timezone", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.Integer(), nullable=False),
        sa.Column("phone_encrypted", sa.String(512), nullable=True),
        sa.Column("full_name", sa.String(200), nullable=True),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("city_id", sa.Integer(), nullable=True),
        sa.Column("rating", sa.Float(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("completed_tasks_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id", name="uq_users_telegram_id"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)
    op.create_index("ix_users_city_id", "users", ["city_id"], unique=False)
    op.create_index("ix_users_city_role", "users", ["city_id", "role"], unique=False)

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("city_id", sa.Integer(), nullable=False),
        sa.Column("address_text", sa.String(500), nullable=False),
        sa.Column("payment_type", sa.String(20), nullable=False),
        sa.Column("payment_amount", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["customer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tasks_customer_id", "tasks", ["customer_id"], unique=False)
    op.create_index("ix_tasks_city_id", "tasks", ["city_id"], unique=False)
    op.create_index("ix_tasks_city_status_created", "tasks", ["city_id", "status", "created_at"], unique=False)

    op.create_table(
        "bids",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("worker_id", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("proposed_amount", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["worker_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id", "worker_id", name="uq_bids_task_worker"),
    )
    op.create_index("ix_bids_task_id", "bids", ["task_id"], unique=False)
    op.create_index("ix_bids_worker_id", "bids", ["worker_id"], unique=False)

    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("from_user_id", sa.Integer(), nullable=False),
        sa.Column("to_user_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["from_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["to_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reviews_task", "reviews", ["task_id"], unique=False)

    op.create_table(
        "verification_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("document_number_encrypted", sa.String(512), nullable=True),
        sa.Column("document_photo_file_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_verification_requests_user_id", "verification_requests", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_verification_requests_user_id", table_name="verification_requests")
    op.drop_table("verification_requests")
    op.drop_index("ix_reviews_task", table_name="reviews")
    op.drop_table("reviews")
    op.drop_index("ix_bids_worker_id", table_name="bids")
    op.drop_index("ix_bids_task_id", table_name="bids")
    op.drop_table("bids")
    op.drop_index("ix_tasks_city_status_created", table_name="tasks")
    op.drop_index("ix_tasks_city_id", table_name="tasks")
    op.drop_index("ix_tasks_customer_id", table_name="tasks")
    op.drop_table("tasks")
    op.drop_index("ix_users_city_role", table_name="users")
    op.drop_index("ix_users_city_id", table_name="users")
    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_table("users")
    op.drop_table("cities")
