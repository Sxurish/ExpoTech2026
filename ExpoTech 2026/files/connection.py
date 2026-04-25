"""
database/connection.py
----------------------
Centralised SQLAlchemy engine + session factory.
All credentials are read from environment variables (or a .env file).
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()


# ---------------------------------------------------------------------------
# Declarative Base — shared by every model
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# DatabaseManager — singleton-style, holds the engine + session factory
# ---------------------------------------------------------------------------
class DatabaseManager:
    """Manages the SQLAlchemy engine and provides session context managers."""

    _instance: "DatabaseManager | None" = None

    def __init__(self) -> None:
        self._engine = self._build_engine()
        self._SessionLocal = sessionmaker(
            bind=self._engine, autocommit=False, autoflush=False,
            expire_on_commit=False,   # keep attributes accessible after session.close()
        )

    # ------------------------------------------------------------------
    # Singleton accessor
    # ------------------------------------------------------------------
    @classmethod
    def get_instance(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------
    # Engine construction
    # ------------------------------------------------------------------
    @staticmethod
    def _build_engine():
        db_user     = os.getenv("DB_USER", "root")
        db_password = os.getenv("DB_PASSWORD", "root")
        db_host     = os.getenv("DB_HOST", "localhost")
        db_port     = os.getenv("DB_PORT", "3306")
        db_name     = os.getenv("DB_NAME", "study_planner")

        url = (
            f"mysql+mysqlconnector://{db_user}:{db_password}"
            f"@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
        )

        engine = create_engine(
            url,
            pool_pre_ping=True,       # detect stale connections
            pool_size=5,
            max_overflow=10,
            echo=False,               # set True for SQL query logging
        )

        # Enforce FK constraints on every new connection
        @event.listens_for(engine, "connect")
        def set_fk_pragma(dbapi_con, _con_record):
            cursor = dbapi_con.cursor()
            cursor.execute("SET FOREIGN_KEY_CHECKS=1")
            cursor.close()

        return engine

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def create_all_tables(self) -> None:
        """Create all tables defined via Base metadata (if they don't exist)."""
        Base.metadata.create_all(bind=self._engine)

    def test_connection(self) -> bool:
        """Return True if the database is reachable, False otherwise."""
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError as exc:
            print(f"[DB] Connection failed: {exc}")
            return False

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Yield a scoped session; commit on success, rollback on error."""
        session: Session = self._SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# ---------------------------------------------------------------------------
# Module-level convenience shortcut
# ---------------------------------------------------------------------------
def get_db() -> DatabaseManager:
    return DatabaseManager.get_instance()
