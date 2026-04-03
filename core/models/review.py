from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Index

from .base import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False, index=True)
    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    task: Mapped["Task"] = relationship("Task", back_populates="reviews")
    from_user: Mapped["User"] = relationship("User", back_populates="reviews_given", foreign_keys=[from_user_id])
    to_user: Mapped["User"] = relationship("User", back_populates="reviews_received", foreign_keys=[to_user_id])

    __table_args__ = (Index("ix_reviews_task", "task_id"),)

    def __repr__(self) -> str:
        return f"<Review(id={self.id}, task_id={self.task_id})>"
