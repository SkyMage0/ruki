from __future__ import annotations

from datetime import datetime
from enum import Enum
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Index

from .base import Base


class TaskCategory(str, Enum):
    moving = "moving"
    cleaning = "cleaning"
    construction = "construction"
    loading = "loading"
    other = "other"


class TaskStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"
    disputed = "disputed"


class PaymentType(str, Enum):
    hourly = "hourly"
    fixed = "fixed"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), nullable=False, index=True)
    address_text: Mapped[str] = mapped_column(String(500), nullable=False)
    payment_type: Mapped[str] = mapped_column(String(20), nullable=False)
    payment_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    workers_needed: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(20), default=TaskStatus.open.value, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_urgent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    customer: Mapped["User"] = relationship("User", back_populates="tasks_as_customer")
    city: Mapped["City"] = relationship("City", back_populates="tasks")
    bids: Mapped[list["Bid"]] = relationship("Bid", back_populates="task")
    reviews: Mapped[list["Review"]] = relationship("Review", back_populates="task")

    __table_args__ = (Index("ix_tasks_city_status_created", "city_id", "status", "created_at"),)

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, status={self.status})>"
