# -*- coding: utf-8 -*-
"""
CLI para Café Electrónico.

Ejecución:
    python -m src.cafe_electronico.cli

Comandos interactivos:
  1 | still                -> evento unitario quieto (+1 min)
  2 | move                 -> reinicia quietud
  rapid N HH:MM            -> simula N min de quietud desde esa hora
  hora HH:MM ev still|move -> fuerza hora + evento unitario
  salir                    -> termina
"""
from __future__ import annotations

from typing import Optional
from datetime import datetime, timedelta
import argparse
import logging
import os

# Importá tu Monitor/Config y el formateo de logs
from .monitor import Config, Monitor
from . import logging_config


# ---------- helpers tolerantes a dict/obj ----------

def _get(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _minutes_from_result(result) -> Optional[int]:
    # nombres posibles que puede devolver el monitor
    for name in ("minutes_still", "minutes", "quiet", "still_minutes", "quiet_minutes", "min_still"):
        v = _get(result, name)
        if isinstance(v, int):
            return v
    return None


def _bool_from_result(obj, name: str, default: bool = False) -> bool:
    v = _get(obj, name, None)
    if isinstance(v, bool):
        return v
    if isinstance(v, int):
        return bool(v)
    return default


def _maybe_str(obj, name: str, default: str = "-") -> str:
    v = _get(obj, name, None)
    return default if v is None else str(v)


# ---------- args ----------

def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="cafe-electronico",
        description="CLI de simulación/control para Café Electrónico",
    )
    p.add_argument("--serial", help="Puerto serie (e.g., COM3)")
    p.add_argument("--baud", type=int, default=9600,
                   help="Baudrate para serie (default: 9600)")
    p.add_argument("--q10", type=int, default=10,
                   help="Umbral Q10 en minutos (default: 10)")
    p.add_argument("--q30", type=int, default=30,
                   help="Umbral Q30 en minutos (default: 30)")
    p.add_argument("--tol-start", default="04:00",
                   help="Inicio franja tolerancia HH:MM (default: 04:00)")
    p.add_argument("--tol-end", default="06:00",
                   help="Fin franja tolerancia HH:MM (default: 06:00)")
    p.add_argument("--csv", default="historial.csv",
                   help="Ruta CSV para registrar ticks")
    return p.parse_args(argv)


# ---------- IO de una línea ----------

def _parse_hhmm(s: str) -> datetime:
    now = datetime.now()
    hh, mm = s.strip().split(":", 1)
    return now.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)


def _print_tick(result, fallback_dt: datetime, ev_name: str) -> None:
    dt = _get(result, "dt", fallback_dt)
    if not isinstance(dt, datetime):
        dt = fallback_dt

    mins = _minutes_from_result(result)
    a = _get(result, "A", None)
    if a is None:
        a = 1 if _bool_from_result(result, "alarm", False) else 0

    reason = _maybe_str(result, "reason", "-")
    human = _maybe_str(result, "human") or _maybe_str(result, "msg")

    hhmm = dt.strftime("%H:%M")
    mins_txt = f"{mins}min" if mins is not None else "?min"
    print(f"{hhmm} ev={ev_name} quietud={mins_txt} A={a} ({reason})")
    print(human)


def _append_csv(cfg, result, fallback_dt: datetime, ev_name: str, csv_fallback: str) -> None:
    # usa Config.csv_path si existe
    path = getattr(cfg, "csv_path", None) or csv_fallback
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    except Exception:
        pass

    dt = _get(result, "dt", fallback_dt)
    if not isinstance(dt, datetime):
        dt = fallback_dt
    mins = _minutes_from_result(result)
    a = _get(result, "A", None)
    if a is None:
        a = 1 if _bool_from_result(result, "alarm", False) else 0

    line = ",".join([
        dt.strftime("%Y-%m-%d %H:%M"),
        ev_name,
        "" if mins is None else str(mins),
        str(a),
    ])
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as exc:
        logging.getLogger(__name__).warning(
            "No se pudo escribir CSV %s: %s", path, exc)


# ---------- modos de ejecución ----------

def _run_keyboard(monitor: Monitor, cfg: Config, csv_path: str) -> int:
    print("Comandos disponibles:")
    print("  1 | still                 -> evento unitario quieto (+1 min)")
    print("  2 | move                  -> reinicia quietud")
    print("  rapid N HH:MM            -> simula N min de quietud en esa hora")
    print("  hora HH:MM ev still|move -> fuerza hora y evento unitario")
    print("  salir                    -> termina")
    print("")

    current_dt = datetime.now().replace(second=0, microsecond=0)
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("")
            return 0

        if not raw:
            continue
        if raw.lower() == "salir":
            return 0

        if raw in ("1", "still"):
            res = monitor.tick(is_still=True, dt=current_dt)
            _print_tick(res, current_dt, "still")
            _append_csv(cfg, res, current_dt, "still", csv_path)
            current_dt += timedelta(minutes=1)
            continue

        if raw in ("2", "move"):
            res = monitor.tick(is_still=False, dt=current_dt)
            _print_tick(res, current_dt, "move")
            _append_csv(cfg, res, current_dt, "move", csv_path)
            current_dt += timedelta(minutes=1)
            continue

        if raw.startswith("rapid "):
            try:
                _, n_s, hhmm = raw.split()
                n = int(n_s)
                base = _parse_hhmm(hhmm)
            except Exception:
                print("Uso: rapid N HH:MM")
                continue
            current_dt = base
            for _ in range(n):
                res = monitor.tick(is_still=True, dt=current_dt)
                _print_tick(res, current_dt, "still")
                _append_csv(cfg, res, current_dt, "still", csv_path)
                current_dt += timedelta(minutes=1)
            continue

        if raw.startswith("hora "):
            try:
                _, hhmm, _, ev = raw.split()
                if ev not in ("still", "move"):
                    raise ValueError
            except Exception:
                print("Uso: hora HH:MM ev still|move")
                continue
            current_dt = _parse_hhmm(hhmm)
            is_still = ev == "still"
            res = monitor.tick(is_still=is_still, dt=current_dt)
            _print_tick(res, current_dt, ev)
            _append_csv(cfg, res, current_dt, ev, csv_path)
            current_dt += timedelta(minutes=1)
            continue

        print("Comando no reconocido. Escribí 'salir' para terminar.")


def _run_serial(monitor: Monitor, cfg: Config, port: str, baud: int, csv_path: str) -> int:
    print(f"Leyendo del puerto serie {port} @ {baud}...")
    print("Formato: 'still' | 'move' | 'still HH:MM' | 'move HH:MM'")
    try:
        # uso simple sin pyserial
        f = open(port, "r", encoding="utf-8", errors="replace")
    except Exception as exc:
        print(
            f"No pude abrir {port}. Si preferís, instalá 'pyserial' y adaptamos la CLI.")
        return 2

    with f:
        current_dt = datetime.now().replace(second=0, microsecond=0)
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            parts = raw.split()
            if parts[0] not in ("still", "move"):
                continue
            ev = parts[0]
            if len(parts) >= 2:
                try:
                    current_dt = _parse_hhmm(parts[1])
                except Exception:
                    pass
            is_still = ev == "still"
            res = monitor.tick(is_still=is_still, dt=current_dt)
            _print_tick(res, current_dt, ev)
            _append_csv(cfg, res, current_dt, ev, csv_path)
            current_dt += timedelta(minutes=1)
    return 0


# ---------- main ----------

def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    logging_config.configure_logging()

    cfg = Config(
        q10_minutes=int(args.q10),
        q30_minutes=int(args.q30),
        tol_start=str(args.tol_start),
        tol_end=str(args.tol_end),
        csv_path=str(args.csv),
    )
    mon = Monitor(cfg)

    if args.serial:
        return _run_serial(mon, cfg, args.serial, int(args.baud), args.csv)
    return _run_keyboard(mon, cfg, args.csv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
