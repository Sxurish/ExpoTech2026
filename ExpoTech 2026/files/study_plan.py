"""
models/study_plan.py
--------------------
SQLAlchemy ORM model for the `study_plans` table.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base


class StudyPlan(Base):
    __tablename__ = "study_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    day_of_week: Mapped[str] = mapped_column(String(20), nullable=False)
    subject_name: Mapped[str] = mapped_column(String(120), nullable=False)
    study_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="study_plans")  # noqa: F821

    # ------------------------------------------------------------------
    def __repr__(self) -> str:
        return (
            f"<StudyPlan id={self.id} day={self.day_of_week!r} "
            f"subject={self.subject_name!r} minutes={self.study_time_minutes}>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "day_of_week": self.day_of_week,
            "subject_name": self.subject_name,
            "study_time_minutes": self.study_time_minutes,
        }
