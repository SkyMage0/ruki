from __future__ import annotations

from datetime import datetime
from enum import Enum
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import UniqueConstraint

from .base import Base


class BidStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class Bid(Base):
    __tablename__ = "bids"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False, index=True)
    worker_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposed_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=BidStatus.pending.value, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    task: Mapped["Task"] = relationship("Task", back_populates="bids")
    worker: Mapped["User"] = relationship("User", back_populates="bids")

    __table_args__ = (UniqueConstraint("task_id", "worker_id", name="uq_bids_task_worker"),)

    def __repr__(self) -> str:
        return f"<Bid(id={self.id}, task_id={self.task_id}, worker_id={self.worker_id})>"
