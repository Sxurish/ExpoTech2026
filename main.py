"""
Root launcher for the Study Planner CLI.

Allows running the app from the repository root with:
    python main.py
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parent
    app_main = repo_root / "ExpoTech 2026" / "files" / "main.py"

    if not app_main.exists():
        raise FileNotFoundError(
            f"Could not find app entrypoint at: {app_main}"
        )

    sys.path.insert(0, str(app_main.parent))
    runpy.run_path(str(app_main), run_name="__main__")


if __name__ == "__main__":
    main()
