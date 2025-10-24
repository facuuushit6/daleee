"""
Configuración base de logging para la aplicación Café Electrónico.
"""

from __future__ import annotations

import logging
import os
from typing import Optional


def configure_logging(level: Optional[str | int] = None) -> None:
    """Configura logging con un formato consistente.

    La prioridad se determina así:
    - `level` explícito si se pasa.
    - variable de entorno `LOG_LEVEL`.
    - por defecto: INFO.
    """

    resolved = _resolve_level(level)
    logging.basicConfig(
        level=resolved,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _resolve_level(user_level: Optional[str | int]) -> int:
    if user_level is not None:
        return _to_numeric_level(user_level)
    env = os.getenv("LOG_LEVEL")
    return _to_numeric_level(env) if env else logging.INFO


def _to_numeric_level(value: str | int) -> int:
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        pass
    return logging.getLevelName(value.upper()) if isinstance(value, str) else logging.INFO

