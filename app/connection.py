"""
connection.py
-------------
SQLAlchemy engine + session factory para Supabase Postgres.

- Lê DATABASE_URL do ambiente (use o connection string do *Connection Pooler*
  na Supabase — porta 6543 — para ambientes serverless).
- Usa NullPool: em serverless cada invocação é efêmera, então não faz sentido
  manter pool de conexões no processo.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()


class Base(DeclarativeBase):
    pass


class DatabaseManager:
    """Singleton-ish acesso ao engine + sessions."""

    _instance: "DatabaseManager | None" = None

    def __init__(self) -> None:
        self._engine = self._build_engine()
        self._SessionLocal = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    @classmethod
    def get_instance(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def _build_engine():
        url = os.getenv("DATABASE_URL")
        if not url:
            raise RuntimeError(
                "DATABASE_URL não definida. Configure o connection string do "
                "Supabase (Project Settings → Database → Connection pooler)."
            )

        if url.startswith("postgres://"):
            url = "postgresql+psycopg2://" + url[len("postgres://"):]
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg2://" + url[len("postgresql://"):]

        return create_engine(
            url,
            poolclass=NullPool,
            pool_pre_ping=True,
            echo=False,
        )

    def test_connection(self) -> bool:
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError as exc:
            print(f"[DB] Connection failed: {exc}")
            return False

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        session: Session = self._SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def get_db() -> DatabaseManager:
    return DatabaseManager.get_instance()
