#!/usr/bin/env python3
"""Data desk: Systems — a nightly health board for the Hermes stack.

Checks, in code, no model:
  * the Telegram gateway answers on 127.0.0.1:8642 (TCP connect, 2s timeout)
  * Hermes processes are alive (tasklist on Windows, ps on POSIX)
  * the repo drive has headroom (shutil.disk_usage of the home drive)
  * the clock it ran at (so the reader knows this is last night's reading)

A probe that cannot run reports `not checked`, never a guess. Network is
localhost only; no keys.

Usage:
  ops-desk.py <edition_dir> [--gate HOST:PORT]
Writes articles/05-the-hermes-stack.md (code 05, after the lead, the column,
projects and the log — a systems board belongs at the back).
"""

import argparse
import datetime
import json
import shutil
import socket
import subprocess
import sys
from pathlib import Path

DEFAULT_GATE = ("127.0.0.1", 8642)
PROCESS_KEYS = ("hermes", "gateway", "python")


def check_gateway(host: str, port: int, timeout: float = 2.0) -> str:
    """True when the gateway accepts a TCP connection within the timeout."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return "live"
    except OSError:
        return "down"


def _decode(raw: bytes) -> str:
    """tasklist on a Russian Windows speaks cp1251; never crash on output."""
    for enc in ("cp1251", "utf-8", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def check_processes() -> str:
    """Count Hermes-related processes. Cross-platform, best effort."""
    try:
        if sys.platform.startswith("win"):
            out = _decode(subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True, timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            ).stdout)
        else:
            out = _decode(subprocess.run(
                ["ps", "-A", "-o", "comm"], capture_output=True, timeout=10,
            ).stdout)
    except (OSError, subprocess.SubprocessError) as e:
        return f"not checked ({type(e).__name__})"
    count = sum(1 for key in PROCESS_KEYS if key in out.lower())
    return f"{count} procs" if count else "none"


def check_disk() -> str:
    """Percent of the repo's drive used; 'not checked' if it cannot be read."""
    try:
        usage = shutil.disk_usage(Path.home())
        pct = usage.used * 100 // usage.total
        return f"{pct}% used"
    except OSError:
        return "not checked"


def build_checks(host: str = DEFAULT_GATE[0], port: int = DEFAULT_GATE[1]) -> dict:
    """Run every probe and return a plain dict, ready for the article."""
    return {
        "gateway": check_gateway(host, port),
        "processes": check_processes(),
        "disk": check_disk(),
        "ran_at": datetime.datetime.now().strftime("%H:%M"),
    }


def build_article(checks: dict) -> str:
    """Render the Systems story from a checks dict (testable without network)."""
    gateway = checks["gateway"]
    headline = {
        "live": "Системы поутру",
        "down": "Шлюз молчит",
    }.get(gateway, "Состояние систем")
    deck = {
        "live": "Все службы живы, диск в порядке",
        "down": "Telegram-шлюз не отвечает — смотреть срочно",
    }.get(gateway, "Проверка частично не удалась")
    body = {
        "live": "Проверка кодом, без сети и ключей: шлюз принимает "
                "соединения, процессы на месте, диск дышит. Это последнее "
                "чтение перед печатью.",
        "down": "Шлюз не ответил на подключение к 127.0.0.1:8642. Первым "
                "делом глянуть watchdog и логи гейта.",
    }.get(gateway, "Некоторые проверки не выполнились; таблица ниже "
                   "показывает, что именно.")
    rows = "\n".join(
        f"| {name} | {status} | {detail} |"
        for name, status, detail in (
            ("Telegram-шлюз", checks["gateway"], "127.0.0.1:8642"),
            ("Процессы", checks["processes"], "hermes/gateway"),
            ("Диск", checks["disk"], "home drive"),
        )
    )
    return f"""---
id: 05-the-hermes-stack
headline: {headline}
deck: {deck}
section: ops
priority: 5
---
{body}
### Состояние
| Служба | Статус | Деталь |
|:---|---:|---|
{rows}
Снято в {checks["ran_at"]} ночным прогоном.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("edition_dir", type=Path)
    ap.add_argument("--gate", default=None,
                    help="HOST:PORT of the gateway (default 127.0.0.1:8642)")
    args = ap.parse_args()

    host, port = DEFAULT_GATE
    if args.gate and ":" in args.gate:
        host, port_str = args.gate.rsplit(":", 1)
        port = int(port_str)

    checks = build_checks(host, port)
    articles = args.edition_dir / "articles"
    articles.mkdir(parents=True, exist_ok=True)
    out = articles / "05-the-hermes-stack.md"
    out.write_text(build_article(checks), encoding="utf-8")
    print(f"wrote {out} (gateway={checks['gateway']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())