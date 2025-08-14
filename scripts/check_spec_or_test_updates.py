#!/usr/bin/env python
"""Warn if code changes lack matching spec or test updates."""
from __future__ import annotations

import subprocess
import sys


def get_staged_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
        check=False,
    )
    files = result.stdout.strip().splitlines()
    return [f for f in files if f]


def main() -> int:
    staged = get_staged_files()
    code_dirs = ("src/", "scripts/")
    code_changes = [
        f
        for f in staged
        if f.endswith(".py") and any(f.startswith(d) for d in code_dirs)
    ]
    if not code_changes:
        return 0
    spec_or_test = [
        f
        for f in staged
        if f.startswith("docs/specifications/") or f.startswith("tests/")
    ]
    if spec_or_test:
        return 0
    print("Warning: code changes detected without accompanying spec or test updates.")
    print(
        "Add or update files in docs/specifications/ or tests/ to maintain traceability."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
