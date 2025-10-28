#!/usr/bin/env python3
"""
Verify pytest can collect tests and plugins load correctly.
Returns non-zero exit code if collection fails.
"""
from __future__ import annotations

import subprocess
import sys
from typing import List


def run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    return subprocess.call(cmd)


def main() -> int:
    rc = run(["poetry", "run", "pytest", "--collect-only", "-q"])  # quiet summary
    if rc == 0:
        print("Pytest collection succeeded.")
    else:
        print("Pytest collection failed.", file=sys.stderr)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
