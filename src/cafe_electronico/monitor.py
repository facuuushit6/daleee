# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from typing import Dict, Tuple
import csv


# ------------------------------
# Config y utilidades de tiempo
# ------------------------------

@dataclass
class Config:
    q10_minutes: int      # umbral Q10 (min)
    q30_minutes: int      # umbral Q30 (min)
    # inicio franja tolerancia (incluyente) - hoy no se usa
    tol_start: str | time
    tol_end: str | time   # fin franja tolerancia (excluyente) - hoy no se usa
    csv_path: str         # ruta del CSV de historial


def _time_flags(dt: datetime) -> Tuple[int, int]:
    """
    Devuelve (M4, M6):
      M4=1 si hora >= 04:00
      M6=1 si hora >= 06:00
    """
    minutes = dt.hour * 60 + dt.minute
    return (1 if minutes >= 4 * 60 else 0,
            1 if minutes >= 6 * 60 else 0)


# ------------------------------
# Monitor principal
# ------------------------------

class Monitor:
    """
    Mantiene el contador de quietud y aplica reglas del Café Electrónico.

    La CLI espera:
      - constructor: Monitor(cfg: Config)
      - método: tick(is_still: bool, dt: datetime) -> dict

    El dict devuelto contiene al menos:
      'is_still','alarm','reason','human','q10','q30','m4','m6','quiet','dt'
    y además alias compatibles:
      'minutes_still'/'minutes'/'quiet', 'A', 'Q10','Q30','M4','M6','msg'
    """

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.quiet_min = 0  # minutos consecutivos quieto

    # ---------- reglas núcleo ----------

    def _eval_alarm(self, q10: int, q30: int, m4: int, m6: int) -> tuple[int, str]:
        """
        Reglas (con protección de don't-care):
          - Si (m6=1 y m4=0) o (q30=1 y q10=0) => A=0
          - Si q30=1 => A=1 (razón 'Q30')
          - Si q10=1 y (m4=0) => A=1 (razón 'Q10&~M4')
          - Si q10=1 y (m6=1) => A=1 (razón 'Q10&M6')
          - Si no => A=0
        """
        if (m6 == 1 and m4 == 0) or (q30 == 1 and q10 == 0):
            return 0, "-"

        if q30 == 1:
            return 1, "Q30"

        if q10 == 1 and (m4 == 0 or m6 == 1):
            return (1, "Q10&~M4") if m4 == 0 else (1, "Q10&M6")

        return 0, "-"

    def _messages(self, q10: int, q30: int, m4: int, m6: int, a: int, reason: str) -> str:
        if a == 1:
            if reason == "Q30":
                return "🔔 ALARMA — Quietud ≥ 30 min (se quedó dormido con seguridad)"
            elif reason == "Q10&~M4":
                return "🔔 ALARMA — Quietud ≥ 10 min antes de las 4:00"
            else:
                return "🔔 ALARMA — Quietud ≥ 10 min después de las 6:00"
        else:
            if (q10 == 1) and (m4 == 1) and (m6 == 0):
                return "⏳ TOLERANCIA — Entre 4:00 y 6:00; se deja dormir un poco"
            return "✅ Todo normal — Sin quietud suficiente o hubo movimiento"

    # ---------- CSV ----------

    def _csv_append(self, row: Dict):
        path = self.cfg.csv_path
        header = ["timestamp", "hora", "min", "evento", "quietud_min",
                  "Q10", "Q30", "M4", "M6", "A", "razon", "msg"]
        new_file = False
        try:
            with open(path, "r", encoding="utf-8"):
                pass
        except FileNotFoundError:
            new_file = True

        with open(path, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new_file:
                w.writerow(header)
            w.writerow([
                row["dt"].isoformat(timespec="minutes"),
                row["dt"].hour,
                row["dt"].minute,
                "still" if row["is_still"] else "move",
                row["quiet"],
                row["q10"], row["q30"], row["m4"], row["m6"],
                1 if row["alarm"] else 0,
                row["reason"],
                row["human"],
            ])

    # ---------- interfaz para la CLI ----------

    def tick(self, is_still: bool, dt: datetime) -> Dict:
        """
        Un “tick” de evaluación. La CLI llama esto por cada evento leído.
        """
        # actualizar contador de quietud
        if is_still:
            self.quiet_min += 1  # +1 minuto por tick unitario
        else:
            self.quiet_min = 0

        # flags y señales
        q10 = 1 if self.quiet_min >= self.cfg.q10_minutes else 0
        q30 = 1 if self.quiet_min >= self.cfg.q30_minutes else 0
        m4, m6 = _time_flags(dt)

        # evaluar alarma
        a, reason = self._eval_alarm(q10, q30, m4, m6)

        # mensaje humano
        human = self._messages(q10, q30, m4, m6, a, reason)

        # construir resultado
        result = {
            "is_still": is_still,
            "alarm": bool(a),
            "reason": reason,
            "human": human,
            "q10": q10,
            "q30": q30,
            "m4": m4,
            "m6": m6,
            "quiet": self.quiet_min,
            "dt": dt,
        }
        # --- ALIAS para compatibilidad con la CLI ---
        result.update({
            "minutes_still": self.quiet_min,   # alias de quiet
            "minutes": self.quiet_min,         # otro alias común
            "A": 1 if a else 0,                # alias entero de alarm
            "Q10": q10,
            "Q30": q30,
            "M4": m4,
            "M6": m6,
            "msg": human,                      # alias de 'human'
        })

        # guardar CSV
        try:
            self._csv_append(result)
        except Exception:
            # no bloquear la app por un error de escritura
            pass

        return result
