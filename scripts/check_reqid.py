#!/usr/bin/env python3
"""Minimal ReqID checker for tests.

Scans tests/ for 'ReqID:' tags in comments/docstrings (advisory-only).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
REQ_RE = re.compile(r"ReqID:\s*[A-Z]+-\d+")


def main() -> int:
    if not TESTS.exists():
        print("[check_reqid] tests/ not found (skipping)")
        return 0
    found = 0
    for p in TESTS.rglob("*.py"):
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if REQ_RE.search(t):
            found += 1
    print(f"[check_reqid] advisory scan done; files with ReqID tags: {found}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
