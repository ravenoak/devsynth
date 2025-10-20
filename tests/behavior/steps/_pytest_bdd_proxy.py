"""Compatibility shim for importing :mod:`pytest_bdd.plugin`.

Historically the behavior step packages exported ``pytest_plugins`` values to
trigger plugin loading. Pytest 8 tightened the rules around nested
declarations, so the root ``tests.conftest`` module now loads plugins via the
central registry. We retain this module solely so legacy imports succeed
without exposing an additional ``pytest_plugins`` attribute.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

try:  # pragma: no cover - defensive import guard
    pytest_bdd_plugin: Any = import_module("pytest_bdd.plugin")
except Exception:  # pragma: no cover - pytest-bdd not installed
    pytest_bdd_plugin = None

__all__ = ["pytest_bdd_plugin"]
