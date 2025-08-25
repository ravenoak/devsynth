#!/usr/bin/env python3
"""Fast syntax error scan over Python source files.

This is a minimal implementation that compiles Python files under src/ and
scripts/ to catch obvious syntax issues. It is fast and deterministic.
"""
from __future__ import annotations

import compileall
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ok = True
    for rel in ("src", "scripts"):
        path = ROOT / rel
        if not path.exists():
            continue
        # quiet=True returns False if errors were found
        if not compileall.compile_dir(str(path), maxlevels=10, quiet=1):
            ok = False
    if not ok:
        print("[find_syntax_errors] syntax errors detected", file=sys.stderr)
        return 1
    print("[find_syntax_errors] OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
