#!/usr/bin/env python3
"""
Helper to install and autoupdate pre-commit hooks.
This is a convenience wrapper to standardize contributor setup.
"""
from __future__ import annotations

import shutil
import subprocess
import sys


def main() -> int:
    exe = shutil.which("pre-commit")
    if not exe:
        print(
            "pre-commit is not installed. Install via 'pipx install pre-commit' or 'pip install pre-commit'",
            file=sys.stderr,
        )
        return 1
    print("Installing pre-commit hooks...")
    rc1 = subprocess.call([exe, "install"])
    print("Autoupdating hooks...")
    rc2 = subprocess.call([exe, "autoupdate"])
    if rc1 == 0 and rc2 == 0:
        print("pre-commit hooks installed and updated.")
        return 0
    print("pre-commit setup encountered errors.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
