"""
auth/auth_service.py
--------------------
Handles user registration and login.
Business logic only — no CLI code here.
"""

from __future__ import annotations

import re

import bcrypt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from user import User


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------
class AuthError(Exception):
    """Base auth error."""


class ValidationError(AuthError):
    """Input validation failed."""


class DuplicateEmailError(AuthError):
    """Email already registered."""


class InvalidCredentialsError(AuthError):
    """Wrong email or password."""


# ---------------------------------------------------------------------------
# AuthService
# ---------------------------------------------------------------------------
class AuthService:
    """Stateless service; receives a SQLAlchemy Session via DI."""

    _EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    _MIN_PASSWORD_LEN = 6

    # ------------------------------------------------------------------
    # Register
    # ------------------------------------------------------------------
    def register(
        self,
        session: Session,
        *,
        full_name: str,
        email: str,
        password: str,
        confirm_password: str,
        education_level: str,
        course: str,
    ) -> User:
        """Create and persist a new user. Returns the saved User object."""
        self._validate_registration(
            full_name=full_name,
            email=email,
            password=password,
            confirm_password=confirm_password,
            education_level=education_level,
            course=course,
        )

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        user = User(
            full_name=full_name.strip(),
            email=email.strip().lower(),
            password=hashed,
            education_level=education_level.strip(),
            course=course.strip(),
        )

        try:
            session.add(user)
            session.flush()   # triggers FK/unique checks before commit
        except IntegrityError:
            # Flush failures leave the Session transaction in an invalid state.
            # Explicit rollback is required before the Session can be reused.
            session.rollback()
            raise DuplicateEmailError(f"Email '{email}' is already registered.")

        return user

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------
    def login(self, session: Session, *, email: str, password: str) -> User:
        """Verify credentials and return the User object."""
        if not email or not password:
            raise ValidationError("Email and password are required.")

        user: User | None = (
            session.query(User).filter_by(email=email.strip().lower()).first()
        )

        if user is None or not bcrypt.checkpw(password.encode(), user.password.encode()):
            raise InvalidCredentialsError("Invalid email or password.")

        return user

    # ------------------------------------------------------------------
    # Internal validation
    # ------------------------------------------------------------------
    def _validate_registration(
        self,
        *,
        full_name: str,
        email: str,
        password: str,
        confirm_password: str,
        education_level: str,
        course: str,
    ) -> None:
        if not full_name or not full_name.strip():
            raise ValidationError("Full name is required.")

        if not self._EMAIL_RE.match(email.strip()):
            raise ValidationError(f"'{email}' is not a valid email address.")

        if len(password) < self._MIN_PASSWORD_LEN:
            raise ValidationError(
                f"Password must be at least {self._MIN_PASSWORD_LEN} characters."
            )

        if password != confirm_password:
            raise ValidationError("Passwords do not match.")

        if not education_level or not education_level.strip():
            raise ValidationError("Education level is required.")

        if not course or not course.strip():
            raise ValidationError("Course is required.")
