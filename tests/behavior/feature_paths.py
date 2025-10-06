"""Utilities for resolving behavior feature file paths."""

from __future__ import annotations

from pathlib import Path


def feature_path(source: str, *parts: str) -> str:
    """Return an absolute path to a feature file relative to ``source``."""

    base = Path(source).resolve().parent
    if base.name == "steps":
        base = base.parent
    return str(base / "features" / Path(*parts))
