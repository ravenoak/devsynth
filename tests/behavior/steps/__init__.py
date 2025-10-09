"""Behavior test step definitions package.

All step modules are imported when this package is loaded so that pytest-bdd
can register every step definition.  The previous lazy-import approach caused
``StepDefinitionNotFound`` errors when step modules were not referenced
explicitly in test files.  Importing everything eagerly keeps collection
reliable without a noticeable performance impact.

Pytest plugin exports now live in :mod:`tests.pytest_plugin_registry` and are
loaded from :mod:`tests.conftest`, matching pytest 8's guidance for
centralized plugin declarations.
"""

from __future__ import annotations


# Provide no-op ``setUpModule`` and ``tearDownModule`` hooks so pytest does not
# attempt to lazy-import these as modules via ``__getattr__`` on this package.
def setUpModule() -> None:  # noqa: N802 - pytest expects this exact name
    """Package-level setup hook for pytest."""


def tearDownModule() -> None:  # noqa: N802 - pytest expects this exact name
    """Package-level teardown hook for pytest."""


import importlib
import sys
from pathlib import Path
from types import ModuleType

# Eagerly importing every step module caused issues during test collection when
# some modules executed ``pytest_bdd.scenarios`` at import time.  This resulted
# in ``IndexError: list index out of range`` because pytest's configuration
# stack was not yet initialized.  To avoid these side effects we no longer
# automatically import all step modules.  Test files explicitly import the
# modules they depend on which keeps collection reliable without forcing all
# modules to be executed here.

_STEP_DIR = Path(__file__).parent


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
