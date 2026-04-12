"""
models/user.py
--------------
SQLAlchemy ORM model for the `users` table.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    education_level: Mapped[str] = mapped_column(String(80), nullable=False)
    course: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    subjects: Mapped[list["Subject"]] = relationship(  # noqa: F821
        "Subject", back_populates="user", cascade="all, delete-orphan"
    )
    study_plans: Mapped[list["StudyPlan"]] = relationship(  # noqa: F821
        "StudyPlan", back_populates="user", cascade="all, delete-orphan"
    )

    # ------------------------------------------------------------------
    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "education_level": self.education_level,
            "course": self.course,
        }
