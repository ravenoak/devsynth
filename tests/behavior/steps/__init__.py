"""Behavior test step definitions package."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType


def __getattr__(name: str) -> ModuleType:
    """Lazily import step modules.

    This allows importing modules without the ``test_`` prefix used on disk
    without importing every module at package import time. It prevents modules
    with costly side effects (for example, those skipping tests at import time)
    from being loaded unless explicitly requested.
    """

    # Attempt regular import first
    try:
        module = importlib.import_module(f".{name}", __name__)
    except ModuleNotFoundError:
        # Fall back to the ``test_`` prefixed module
        prefixed = f"test_{name}"
        module = importlib.import_module(f".{prefixed}", __name__)
    sys.modules[f"{__name__}.{name}"] = module
    return module
