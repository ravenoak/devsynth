#!/usr/bin/env python3
"""
Static check to enforce that the domain layer is free of framework and adapter dependencies.

Policy:
- Files under src/devsynth/domain/ must not import the following (non-exhaustive):
  typer, fastapi, nicegui, httpx, requests, sqlalchemy, chromadb, faiss, kuzu, lmdb

Usage:
  poetry run python scripts/check_domain_dependencies.py [--report]

Exit codes:
  0 - No violations
  1 - Violations found

Supports docs/tasks.md item 8.1 (audit) and the invariants in docs/architecture/overview.md.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAIN_DIR = ROOT / "src" / "devsynth" / "domain"

FORBIDDEN = {
    "typer",
    "fastapi",
    "nicegui",
    "httpx",
    "requests",
    "sqlalchemy",
    "chromadb",
    "faiss",
    "kuzu",
    "lmdb",
}

IMPORT_RE = re.compile(r"^\s*(from\s+([\w\.]+)\s+import|import\s+([\w\.]+))")


def scan_file(path: Path) -> list[tuple[int, str]]:
    violations: list[tuple[int, str]] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    for lineno, line in enumerate(text.splitlines(), start=1):
        m = IMPORT_RE.match(line)
        if not m:
            continue
        # Extract top-level module
        module = (m.group(2) or m.group(3) or "").split(".")[0]
        if module in FORBIDDEN:
            violations.append((lineno, line.rstrip()))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true", help="Print a report")
    args = parser.parse_args()

    all_violations: list[tuple[Path, int, str]] = []
    for path in DOMAIN_DIR.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        v = scan_file(path)
        for lineno, line in v:
            all_violations.append((path.relative_to(ROOT), lineno, line))

    if args.report or all_violations:
        print("Domain dependency audit results:")
        if not all_violations:
            print("  OK: No forbidden imports found in src/devsynth/domain/")
        else:
            for path, lineno, line in all_violations:
                print(f"  {path}:{lineno}: {line}")

    if all_violations:
        print(
            "ERROR: Forbidden dependencies imported in domain layer.", file=sys.stderr
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
