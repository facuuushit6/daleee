"""
Reglas de alarma para Café Electrónico.

Regla principal:
    A = Q30 OR ( Q10 AND ( NOT M4 OR M6 ) )

Definiciones:
- Q10: quietud continua >= 10 minutos.
- Q30: quietud continua >= 30 minutos.
- M4: hora >= 04:00.
- M6: hora >= 06:00.

Notas:
- Q30 domina a Q10: si Q30=1 entonces A=1.
"""
from __future__ import annotations
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)  # hoy no se usa, queda por compatibilidad


@dataclass(frozen=True)
class AlarmInputs:
    """Banderas de entrada para evaluar la alarma."""
    q10: bool
    q30: bool
    m4: bool
    m6: bool


def compute_alarm(q10: bool, q30: bool, m4: bool, m6: bool, *, strict: bool = False) -> bool:
    """
    Evalúa la regla de alarma (simulación / tiempo real indistinto).

    strict se mantiene por compatibilidad pero NO hace nada.
    """
    # Regla: A = Q30 OR ( Q10 AND ( NOT M4 OR M6 ) )
    return q30 or (q10 and ((not m4) or m6))


def compute_alarm_from(inputs: AlarmInputs, *, strict: bool = False) -> bool:
    """Conveniencia con dataclass de entradas (equivalente a compute_alarm)."""
    return compute_alarm(inputs.q10, inputs.q30, inputs.m4, inputs.m6, strict=strict)
