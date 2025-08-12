#!/usr/bin/env python3
"""Verify that project version references stay synchronized.

The script compares the version declared in ``pyproject.toml`` with the
``__version__`` constant in ``src/devsynth/__init__.py`` and with the
``version`` fields in Markdown document headers.  It exits with status 1 if
any discrepancies are found.
"""
from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _pyproject_version() -> str:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text())
    return data["tool"]["poetry"]["version"]


def _package_version() -> str:
    text = (ROOT / "src" / "devsynth" / "__init__.py").read_text()
    match = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    if not match:
        raise RuntimeError("__version__ not found in src/devsynth/__init__.py")
    return match.group(1)


def _doc_versions() -> dict[Path, str]:
    versions: dict[Path, str] = {}
    for path in ROOT.rglob("*.md"):
        if any(
            part in {".git", "inspirational_docs", "external_research_papers"}
            for part in path.parts
        ):
            continue
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        parts = text.split("---", 2)
        if len(parts) < 3:
            continue
        try:
            front_matter = yaml.safe_load(parts[1])
        except Exception:
            continue
        if isinstance(front_matter, dict) and "version" in front_matter:
            versions[path] = str(front_matter["version"])
    return versions


def main() -> int:
    pyproject_version = _pyproject_version()
    package_version = _package_version()
    mismatches = []
    if package_version != pyproject_version:
        mismatches.append((Path("src/devsynth/__init__.py"), package_version))
    for path, version in _doc_versions().items():
        if version != pyproject_version:
            mismatches.append((path, version))
    if mismatches:
        print("Version mismatches found:")
        for path, version in mismatches:
            print(f"- {path} ({version}) != {pyproject_version}")
        return 1
    print(f"All versions are synchronized: {pyproject_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
