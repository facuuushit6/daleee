"""
Reglas de alarma para Café Electrónico.

Regla principal (según spec):
    A = Q30 OR ( Q10 AND ( NOT M4 OR M6 ) )

Definiciones:
- Q10: quietud continua >= 10 minutos.
- Q30: quietud continua >= 30 minutos.
- M4: hora >= 04:00.
- M6: hora >= 06:00.

Notas:
- Q30 domina a Q10: si Q30=1 entonces A=1.
- Combinaciones inválidas: M6=1 con M4=0; Q30=1 con Q10=0.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AlarmInputs:
    """Banderas de entrada para evaluar la alarma.

    Atributos:
    - q10: bool, quietud continua >= 10 minutos.
    - q30: bool, quietud continua >= 30 minutos.
    - m4: bool, hora >= 04:00.
    - m6: bool, hora >= 06:00.
    """

    q10: bool
    q30: bool
    m4: bool
    m6: bool


def compute_alarm(q10: bool, q30: bool, m4: bool, m6: bool, *, strict: bool = False) -> bool:
    """Evalúa la regla de alarma.

    Implementa: A = Q30 OR ( Q10 AND ( NOT M4 OR M6 ) )

    Parámetros:
    - q10, q30, m4, m6: banderas de entrada.
    - strict: si True, valida combinaciones inválidas y lanza ValueError.

    Retorna:
    - bool: estado de la alarma A.
    """

    if strict:
        _validate_combinations(q10=q10, q30=q30, m4=m4, m6=m6)
    else:
        _warn_on_inconsistent(q10=q10, q30=q30, m4=m4, m6=m6)

    a = q30 or (q10 and ((not m4) or m6))
    return a


def compute_alarm_from(inputs: AlarmInputs, *, strict: bool = False) -> bool:
    """Versión conveniente con dataclass de entradas."""

    return compute_alarm(inputs.q10, inputs.q30, inputs.m4, inputs.m6, strict=strict)


def _validate_combinations(*, q10: bool, q30: bool, m4: bool, m6: bool) -> None:
    """Valida combinaciones marcadas como inválidas en el spec.

    - M6=1 y M4=0 (inconsistente)
    - Q30=1 y Q10=0 (inconsistente)
    """

    errors: list[str] = []
    if m6 and not m4:
        errors.append("Combinación inválida: M6=1 y M4=0")
    if q30 and not q10:
        errors.append("Combinación inválida: Q30=1 y Q10=0")
    if errors:
        raise ValueError("; ".join(errors))


def _warn_on_inconsistent(*, q10: bool, q30: bool, m4: bool, m6: bool) -> None:
    """Registra warnings por combinaciones inconsistentes sin interrumpir."""

    if m6 and not m4:
        logger.warning("Entrada inconsistente detectada: M6=1 y M4=0")
    if q30 and not q10:
        logger.warning("Entrada inconsistente detectada: Q30=1 y Q10=0")

