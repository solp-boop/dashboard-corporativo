"""Logging centralizado.

Los errores técnicos se registran acá (en Streamlit Cloud se ven en
"Manage app" → logs). Al usuario final nunca se le muestra un traceback.
"""
from __future__ import annotations

import logging
import sys

_CONFIGURED = False


def get_logger(name: str = "dashboard") -> logging.Logger:
    global _CONFIGURED
    if not _CONFIGURED:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
        )
        root = logging.getLogger("dashboard")
        root.setLevel(logging.INFO)
        root.addHandler(handler)
        root.propagate = False
        _CONFIGURED = True
    return logging.getLogger(name if name.startswith("dashboard") else f"dashboard.{name}")
