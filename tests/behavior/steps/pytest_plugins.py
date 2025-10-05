"""Central registry for pytest plugins used by behavior step packages."""

from __future__ import annotations

# Empty by default; tests/conftest.py imports this module to satisfy pytest 8's
# requirement that plugin declarations live outside package ``__init__`` files.
PYTEST_PLUGINS: list[str] = []
