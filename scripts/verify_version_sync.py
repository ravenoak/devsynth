#!/usr/bin/env python3
"""Verify that project version is synchronized across metadata sources.

Checks that:
- pyproject.toml [tool.poetry].version matches src/devsynth/__init__.py __version__
- README.md badge/version occurrences match the same version (best effort)

This is intentionally conservative and fast. It prints discrepancies and exits 1
on mismatch, 0 otherwise.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
PKG_INIT = ROOT / "src" / "devsynth" / "__init__.py"
README = ROOT / "README.md"


def read_version_from_pyproject() -> str | None:
    text = PYPROJECT.read_text(encoding="utf-8")
    m = re.search(r"^version\s*=\s*\"([^\"]+)\"", text, re.MULTILINE)
    return m.group(1) if m else None


def read_version_from_init() -> str | None:
    text = PKG_INIT.read_text(encoding="utf-8")
    m = re.search(r"^__version__\s*=\s*\"([^\"]+)\"", text, re.MULTILINE)
    return m.group(1) if m else None


def check_readme_version(ver: str) -> bool:
    if not README.exists():
        return True
    text = README.read_text(encoding="utf-8", errors="ignore")
    # Heuristic: expect version string somewhere in README
    return ver in text


def main() -> int:
    errors: list[str] = []
    pver = read_version_from_pyproject()
    iver = read_version_from_init()

    if not pver:
        errors.append("[verify_version_sync] version missing in pyproject.toml")
    if not iver:
        errors.append(
            "[verify_version_sync] __version__ missing in src/devsynth/__init__.py"
        )

    if pver and iver and pver != iver:
        errors.append(
            f"[verify_version_sync] mismatch: pyproject={pver} != __init__={iver}"
        )

    if pver and not check_readme_version(pver):
        errors.append("[verify_version_sync] README does not reference project version")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print(f"[verify_version_sync] OK version={pver}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
