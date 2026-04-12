"""
services/subject_service.py
----------------------------
Business logic for managing subjects.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from models.subject import Subject


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------
class SubjectError(Exception):
    """Base subject error."""


class SubjectValidationError(SubjectError):
    """Input validation failed."""


# ---------------------------------------------------------------------------
# SubjectService
# ---------------------------------------------------------------------------
class SubjectService:
    """CRUD + validation for Subject entities."""

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------
    def add_subject(
        self,
        session: Session,
        *,
        user_id: int,
        name: str,
        difficulty: int,
        priority: int,
        exam_date_str: str,
    ) -> Subject:
        """Validate input, persist and return a new Subject."""
        self._validate(
            name=name,
            difficulty=difficulty,
            priority=priority,
            exam_date_str=exam_date_str,
        )

        exam_date = date.fromisoformat(exam_date_str)

        subject = Subject(
            user_id=user_id,
            name=name.strip(),
            difficulty=difficulty,
            priority=priority,
            exam_date=exam_date,
        )
        session.add(subject)
        session.flush()
        return subject

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    def get_subjects_for_user(self, session: Session, user_id: int) -> list[Subject]:
        return (
            session.query(Subject)
            .filter_by(user_id=user_id)
            .order_by(Subject.exam_date)
            .all()
        )

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------
    def delete_subject(self, session: Session, subject_id: int, user_id: int) -> bool:
        subject = (
            session.query(Subject)
            .filter_by(id=subject_id, user_id=user_id)
            .first()
        )
        if subject is None:
            return False
        session.delete(subject)
        session.flush()
        return True

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    @staticmethod
    def _validate(
        *,
        name: str,
        difficulty: int,
        priority: int,
        exam_date_str: str,
    ) -> None:
        if not name or not name.strip():
            raise SubjectValidationError("Subject name is required.")

        if not (1 <= difficulty <= 5):
            raise SubjectValidationError("Difficulty must be between 1 and 5.")

        if not (1 <= priority <= 5):
            raise SubjectValidationError("Priority must be between 1 and 5.")

        try:
            parsed = date.fromisoformat(exam_date_str)
        except ValueError:
            raise SubjectValidationError(
                f"Invalid date '{exam_date_str}'. Use YYYY-MM-DD format."
            )

        if parsed < date.today():
            raise SubjectValidationError("Exam date cannot be in the past.")
