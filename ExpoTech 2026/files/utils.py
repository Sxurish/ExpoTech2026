"""
cli/utils.py
------------
Reusable helpers for the command-line interface.
"""

from __future__ import annotations

import getpass
import os

# ANSI colours (fall back gracefully on Windows without colorama)
_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_GREEN  = "\033[92m"
_YELLOW = "\033[93m"
_RED    = "\033[91m"
_CYAN   = "\033[96m"


def _c(text: str, code: str) -> str:
    return f"{code}{text}{_RESET}"


def banner(title: str) -> None:
    width = 60
    print()
    print(_c("═" * width, _CYAN))
    print(_c(f"  {title}", _BOLD + _CYAN))
    print(_c("═" * width, _CYAN))


def section(title: str) -> None:
    print()
    print(_c(f"── {title} ", _BOLD + _YELLOW) + _c("─" * (46 - len(title)), _YELLOW))


def success(msg: str) -> None:
    print(_c(f"  ✓  {msg}", _GREEN))


def error(msg: str) -> None:
    print(_c(f"  ✗  {msg}", _RED))


def info(msg: str) -> None:
    print(f"     {msg}")


def prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"  {label}{suffix}: ").strip()
    return value or default


def prompt_int(label: str, min_val: int, max_val: int) -> int:
    while True:
        raw = prompt(f"{label} ({min_val}–{max_val})")
        try:
            val = int(raw)
            if min_val <= val <= max_val:
                return val
            error(f"Por favor, digite um número entre {min_val} e {max_val}.")
        except ValueError:
            error("Por favor, digite um número inteiro válido.")


def prompt_float(label: str, min_val: float, max_val: float) -> float:
    while True:
        raw = prompt(f"{label} ({min_val}–{max_val})")
        try:
            val = float(raw)
            if min_val <= val <= max_val:
                return val
            error(f"Por favor, digite um número entre {min_val} e {max_val}.")
        except ValueError:
            error("Por favor, digite um número válido.")


def prompt_password(label: str = "Senha") -> str:
    # Usando input() simples para compatibilidade com todos os terminais Windows
    return input(f"  {label}: ")


def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def format_minutes(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    if h and m:
        return f"{h}h {m:02d}min"
    if h:
        return f"{h}h"
    return f"{m}min"
