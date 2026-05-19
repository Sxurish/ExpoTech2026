"""
study_plan.py
-------------
ORM model para a tabela `study_plans` (Postgres + Supabase Auth).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from connection import Base


class StudyPlan(Base):
    __tablename__ = "study_plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    day_of_week: Mapped[str] = mapped_column(String(20), nullable=False)
    subject_name: Mapped[str] = mapped_column(String(120), nullable=False)
    study_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<StudyPlan id={self.id} day={self.day_of_week!r} "
            f"subject={self.subject_name!r} minutes={self.study_time_minutes}>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": str(self.user_id),
            "day_of_week": self.day_of_week,
            "subject_name": self.subject_name,
            "study_time_minutes": self.study_time_minutes,
        }
