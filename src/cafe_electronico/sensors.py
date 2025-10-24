"""
Abstracciones e interfaces de sensores de actividad/quietud y reloj.

Incluye protocolos para desacoplar fuentes reales y utilidades
para calcular M4/M6 desde un `datetime`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from typing import Protocol, runtime_checkable


@runtime_checkable
class MotionSensor(Protocol):
    """Provee una lectura booleana de quietud."""

    def is_still(self) -> bool:  # pragma: no cover - interfaz
        """Devuelve True si el sensor detecta quietud en el tick actual."""


@runtime_checkable
class TimeSource(Protocol):
    """Provee el tiempo actual."""

    def now(self) -> datetime:  # pragma: no cover - interfaz
        """Devuelve la fecha/hora actual."""


@dataclass(frozen=True)
class TimeFlags:
    """Banderas M4/M6 derivadas de un instante temporal."""

    m4: bool
    m6: bool


def compute_time_flags(dt: datetime) -> TimeFlags:
    """Calcula M4 y M6 según la hora del día (>= 04:00 y >= 06:00)."""

    t = dt.time()
    return TimeFlags(m4=_is_on_or_after(t, time(4, 0)), m6=_is_on_or_after(t, time(6, 0)))


def _is_on_or_after(t: time, ref: time) -> bool:
    return (t.hour, t.minute, t.second, t.microsecond) >= (
        ref.hour,
        ref.minute,
        ref.second,
        ref.microsecond,
    )

