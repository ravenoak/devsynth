"""Legacy compatibility module for behavior test plugins.

Pytest now discovers plugins from :mod:`tests.conftest`, which in turn
consults :mod:`tests.pytest_plugin_registry`. This module remains so imports
such as ``import tests.behavior.steps.pytest_plugins`` continue to work, but it
no longer defines ``pytest_plugins`` itself.
"""

from __future__ import annotations

from tests.pytest_plugin_registry import PYTEST_PLUGINS

__all__ = ["PYTEST_PLUGINS"]
