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
    app_main = repo_root / "app" / "main.py"

    if not app_main.exists():
        raise FileNotFoundError(
            f"Could not find app entrypoint at: {app_main}"
        )

    app_dir = str(app_main.parent)
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

    runpy.run_path(str(app_main), run_name="__main__")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n     Interrupted. Goodbye!")
        sys.exit(0)
