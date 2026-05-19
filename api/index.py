"""
Vercel serverless entry-point.
Apenas reexpõe o WSGI app definido em app/api.py.
"""

from __future__ import annotations

import os
import sys

# Adiciona /app ao sys.path para que os módulos do projeto resolvam.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))

from api import app  # noqa: E402  (Flask WSGI app)
