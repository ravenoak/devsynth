#!/usr/bin/env python3
"""Verify release readiness via dialectical audit log.

The script exits with status 1 when ``dialectical_audit.log`` contains
unresolved questions or is missing.  A successful run indicates that the
project's dialectical audit has no outstanding items.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "dialectical_audit.log"


def main() -> int:
    if not LOG_PATH.exists():
        print("dialectical_audit.log not found.")
        return 1
    data = json.loads(LOG_PATH.read_text(encoding="utf-8"))
    questions = data.get("questions", [])
    if questions:
        print("Unresolved questions remain in dialectical_audit.log:")
        for q in questions:
            print(f"- {q}")
        return 1
    print("dialectical_audit.log contains no unresolved questions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
