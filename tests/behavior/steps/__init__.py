"""Behavior test step definitions package."""

from __future__ import annotations

# Pytest inspects packages for a ``pytest_plugins`` variable when importing test
# modules.  Without this variable defined, ``pytest`` attempts to import a
# ``pytest_plugins`` *module* from this package which triggers our ``__getattr__``
# loader and results in ``ModuleNotFoundError`` during test collection.  Export
# an empty list so pytest does not try to load a missing module.
pytest_plugins: list[str] = []

# Provide no-op ``setUpModule`` and ``tearDownModule`` hooks so pytest does not
# attempt to lazy-import these as modules via ``__getattr__`` on this package.
def setUpModule() -> None:  # noqa: N802 - pytest expects this exact name
    """Package-level setup hook for pytest."""


def tearDownModule() -> None:  # noqa: N802 - pytest expects this exact name
    """Package-level teardown hook for pytest."""

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
