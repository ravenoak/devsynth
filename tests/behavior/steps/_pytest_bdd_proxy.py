"""Proxy plugin to load pytest-bdd exactly once."""

from __future__ import annotations

from importlib import import_module

import pytest

_PLUGIN_NAME = "pytest_bdd.plugin"
_PLUGIN_ENTRYPOINT = "pytest-bdd"


def pytest_configure(config: pytest.Config) -> None:
    """Ensure pytest-bdd is registered under a single canonical name."""

    pluginmanager = config.pluginmanager

    if pluginmanager.hasplugin(_PLUGIN_NAME) or pluginmanager.hasplugin(
        _PLUGIN_ENTRYPOINT
    ):
        return

    module = import_module(_PLUGIN_NAME)
    pluginmanager.register(module, _PLUGIN_NAME)
