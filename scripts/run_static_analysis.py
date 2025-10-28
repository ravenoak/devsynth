#!/usr/bin/env python3
"""
run_static_analysis.py

Run mypy with the project's configuration. Prints friendly guidance if
mypy is not installed or configuration is missing. Exits non-zero on type errors.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from typing import List


def run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    return subprocess.call(cmd)


def main() -> int:
    mypy = shutil.which("mypy")
    if not mypy:
        print("mypy not found. Install dev dependencies: poetry install --with dev")
        return 2

    # Use pyproject.toml config by default
    return run(
        [mypy, "--config-file", "pyproject.toml", "src/devsynth"]
    )  # adjust path if needed


if __name__ == "__main__":
    raise SystemExit(main())
