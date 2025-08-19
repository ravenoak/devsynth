"""Helper script to bump project version and sync package metadata."""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
INIT_FILE = ROOT / "src" / "devsynth" / "__init__.py"


def update_init(version: str, init_path: pathlib.Path = INIT_FILE) -> None:
    """Rewrite ``__version__`` in ``__init__.py`` to match the new version."""
    pattern = re.compile(r'(__version__\s*=\s*")([^"]+)(")')
    text = init_path.read_text()
    new_text = pattern.sub(rf"\1{version}\3", text)
    init_path.write_text(new_text)


def bump_version(version: str, init_path: pathlib.Path = INIT_FILE) -> None:
    """Run ``poetry version`` and update ``__init__.py``."""
    subprocess.run(["poetry", "version", version], check=True)
    update_init(version, init_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bump project version")
    parser.add_argument("version", help="New version string")
    args = parser.parse_args()
    bump_version(args.version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
