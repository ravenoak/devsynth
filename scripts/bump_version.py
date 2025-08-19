#!/usr/bin/env python
"""Synchronize project version between Poetry and package metadata."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INIT_FILE = ROOT / "src" / "devsynth" / "__init__.py"


def run_poetry_version(version: str) -> None:
    """Run ``poetry version`` with the provided version."""
    subprocess.run(["poetry", "version", version], check=True)


def update_init(version: str) -> None:
    """Update ``__version__`` in :mod:`devsynth` package."""
    text = INIT_FILE.read_text(encoding="utf-8")
    new_text = re.sub(r'(__version__\s*=\s*")[^"]+("\n)', rf"\1{version}\2", text)
    INIT_FILE.write_text(new_text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bump project version and sync metadata"
    )
    parser.add_argument("version", help="Target version, e.g., 0.1.0-alpha.2.dev0")
    args = parser.parse_args()
    run_poetry_version(args.version)
    update_init(args.version)


if __name__ == "__main__":
    main()
