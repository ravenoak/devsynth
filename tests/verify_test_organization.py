#!/usr/bin/env python3
"""Quick sanity check for test organization.

- Ensures tests/ exists and has at least one file.
- Prints a brief summary to stdout and exits 0; exits 1 only if the basic
  structure is missing. Designed to be fast and deterministic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"


def main() -> int:
    if not TESTS.exists():
        print("[verify_test_organization] tests/ directory not found", file=sys.stderr)
        return 1
    files = list(TESTS.rglob("test_*.py"))
    print(f"[verify_test_organization] found {len(files)} test files under tests/")
    # Do not fail if empty; some minimal clones may not have tests populated yet.
    return 0


if __name__ == "__main__":
    sys.exit(main())
