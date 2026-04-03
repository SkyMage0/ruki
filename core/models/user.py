from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .bid import Bid
from .city import City
from .review import Review
from .task import Task
from .verification import VerificationRequest


class UserRole(str, Enum):
    customer = "customer"
    worker = "worker"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    phone_encrypted: Mapped[str | None] = mapped_column(String(512), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default=UserRole.customer.value, nullable=False)
    city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.id"), nullable=True, index=True)
    rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_tasks_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    last_activity: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    city: Mapped[City] = relationship("City", back_populates="users")
    tasks_as_customer: Mapped[list[Task]] = relationship(
        "Task", back_populates="customer", foreign_keys="Task.customer_id"
    )
    bids: Mapped[list[Bid]] = relationship("Bid", back_populates="worker")
    reviews_received: Mapped[list[Review]] = relationship(
        "Review", back_populates="to_user", foreign_keys="Review.to_user_id"
    )
    reviews_given: Mapped[list[Review]] = relationship(
        "Review", back_populates="from_user", foreign_keys="Review.from_user_id"
    )
    verification_requests: Mapped[list[VerificationRequest]] = relationship(
        "VerificationRequest", back_populates="user"
    )

    __table_args__ = (Index("ix_users_city_role", "city_id", "role"),)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id})>"
