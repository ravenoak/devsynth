#!/usr/bin/env python3
"""
Append a structured execution log entry to diagnostics/exec_log.txt.

Usage:
  poetry run python scripts/append_exec_log.py --command "poetry run pytest -q" --exit-code 0 --notes "smoke run"

Notes:
- Keeps a simple, human-readable format with ISO 8601 timestamp.
- Creates diagnostics/ directory if missing.
- Avoids heavy imports to keep usable in minimal environments.
"""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path


def append_entry(
    command: str, exit_code: int, artifacts: str | None, notes: str | None
) -> None:
    ts = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    diagnostics_dir = Path("diagnostics")
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    log_file = diagnostics_dir / "exec_log.txt"

    lines = [
        f"timestamp: {ts}",
        f"command: {command}",
        f"exit_code: {exit_code}",
    ]
    if artifacts:
        lines.append(f"artifacts: {artifacts}")
    if notes:
        lines.append(f"notes: {notes}")
    lines.append("---")

    with log_file.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Append an execution log entry")
    parser.add_argument("--command", required=True, help="Command that was executed")
    parser.add_argument(
        "--exit-code", type=int, required=True, help="Exit code of the command"
    )
    parser.add_argument(
        "--artifacts", help="Comma-separated artifact paths", default=None
    )
    parser.add_argument("--notes", help="Optional notes", default=None)
    args = parser.parse_args()

    append_entry(
        command=args.command,
        exit_code=args.exit_code,
        artifacts=args.artifacts,
        notes=args.notes,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
