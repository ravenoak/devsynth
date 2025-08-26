"""
Resource and property-testing helpers used by pytest collection hooks.

Extracted from tests/conftest.py to improve maintainability (docs/tasks.md #61).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:  # pragma: no cover - optional dependency
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore


def is_property_testing_enabled() -> bool:
    """Return True if property-based tests should run.

    Checks the DEVSYNTH_PROPERTY_TESTING env var first. If unset, falls back to
    reading config/default.yml's formalVerification.propertyTesting when PyYAML
    is available; otherwise defaults to False.
    """
    flag = os.environ.get("DEVSYNTH_PROPERTY_TESTING")
    if flag is not None:
        return flag.strip().lower() in {"1", "true", "yes"}

    # Fall back to project config if available
    cfg_path = Path(__file__).resolve().parents[2] / "config" / "default.yml"
    if yaml is None:
        return False
    try:
        with open(cfg_path, "r") as f:  # type: ignore[call-arg]
            data: dict[str, Any] = yaml.safe_load(f) or {}
        return bool(data.get("formalVerification", {}).get("propertyTesting", False))
    except Exception:
        return False
