#!/usr/bin/env python3
"""
Verify alignment between pytest resource markers and availability flags.

This script scans the test suite for uses of @pytest.mark.requires_resource("<name>")
and validates that each referenced resource has a corresponding checker implemented
in tests/conftest.py:is_resource_available checker_map.

Usage:
  poetry run python scripts/verify_resource_markers.py [--report]

Exit codes:
  0 - All resource markers are recognized
  1 - One or more unknown resource names found

Notes:
- This supports docs/tasks.md item 15.1.
- It is non-invasive and safe to run locally or in CI.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = ROOT / "tests"
CONFTEST = TESTS_DIR / "conftest.py"

RESOURCE_REGEX = re.compile(
    r"requires_resource\((?:name=)?[\'\"]([A-Za-z0-9_\-]+)[\'\"]\)"
)


def parse_known_resources() -> set[str]:
    """Parse the checker_map in tests/conftest.py to learn known resource names."""
    text = CONFTEST.read_text(encoding="utf-8")
    # Find the checker_map literal block
    # We look for lines under `checker_map = {` until the closing `}`
    known: set[str] = set()
    in_map = False
    for line in text.splitlines():
        if line.strip().startswith("checker_map = {"):
            in_map = True
            continue
        if in_map:
            if line.strip().startswith("}"):
                break
            # lines like: "  'chromadb': is_chromadb_available,"
            parts = line.split(":", 1)
            if len(parts) == 2:
                key = parts[0].strip().strip(",").strip()
                # strip quotes
                if (key.startswith("'") and key.endswith("'")) or (
                    key.startswith('"') and key.endswith('"')
                ):
                    key = key[1:-1]
                if key:
                    known.add(key)
    return known


def find_used_resources() -> set[str]:
    """Scan tests for requires_resource("<name>") occurrences."""
    used: set[str] = set()
    for path in TESTS_DIR.rglob("*.py"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in RESOURCE_REGEX.finditer(text):
            used.add(m.group(1))
    return used


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true", help="Print a report table")
    args = parser.parse_args()

    known = parse_known_resources()
    used = find_used_resources()

    unknown = sorted(used - known)

    if args.report:
        print("Known resources (from tests/conftest.py):", ", ".join(sorted(known)))
        print("Used resources (from tests/):", ", ".join(sorted(used)))
        if unknown:
            print("Unknown resources detected:", ", ".join(unknown))
        else:
            print("All used resources are recognized.")

    if unknown:
        print(
            "ERROR: Unknown resource marker names found (no checker in tests/conftest.py):",
            ", ".join(unknown),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
