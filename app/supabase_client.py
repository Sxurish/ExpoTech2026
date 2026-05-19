"""
supabase_client.py
------------------
Helpers para Supabase Auth no backend:
- valida JWT (Authorization: Bearer <token>) e devolve o user_id (UUID).

Importante para serverless: o cliente é criado por request (não há estado
global de sessão), porque cada invocação valida um JWT diferente.
"""

from __future__ import annotations

import os
from functools import lru_cache

from supabase import Client, create_client


def _env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variável de ambiente {name} não definida.")
    return value


@lru_cache(maxsize=1)
def _anon_client() -> Client:
    """Cliente público (apenas para chamar auth.get_user)."""
    return create_client(_env("SUPABASE_URL"), _env("SUPABASE_ANON_KEY"))


def get_user_id_from_jwt(jwt: str) -> str | None:
    """Retorna o UUID do usuário se o JWT for válido; senão None."""
    try:
        resp = _anon_client().auth.get_user(jwt)
    except Exception:
        return None
    user = getattr(resp, "user", None)
    if user is None:
        return None
    return str(user.id)
