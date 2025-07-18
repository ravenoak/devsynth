"""Utilities to mock heavy optional dependencies during tests."""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock

_HEAVY_MODULES = [
    "sympy",
    "torch",
    "transformers",
]


def apply_lightweight_imports() -> None:
    """Insert lightweight mocks for heavy modules."""
    for name in _HEAVY_MODULES:
        sys.modules[name] = MagicMock(spec=ModuleType(name))
