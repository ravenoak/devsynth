"""Central registry for pytest plugin declarations used by the test suite."""

from __future__ import annotations

from typing import Iterable

# ``pytest_bdd.plugin`` is proxied through ``tests.behavior.steps._pytest_bdd_proxy``
# so behavior step modules can import pytest-bdd helpers without triggering the
# plugin's import-time side effects multiple times.  The registry intentionally
# keeps the canonical plugin name; ``tests.conftest`` applies redirects when
# loading plugins so pytest receives the proxy module.
_PYTEST_PLUGIN_NAMES: tuple[str, ...] = ("pytest_bdd.plugin",)


def iter_pytest_plugins() -> Iterable[str]:
    """Yield plugin entry points for pytest."""

    yield from _PYTEST_PLUGIN_NAMES


PYTEST_PLUGINS: tuple[str, ...] = tuple(iter_pytest_plugins())
"""Canonical list consumed by ``tests.conftest`` for plugin registration."""
