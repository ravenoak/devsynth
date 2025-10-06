"""Compatibility shim that re-exports the shared pytest plugin registry."""

from __future__ import annotations

from tests.pytest_plugin_registry import PYTEST_PLUGINS

__all__ = ["PYTEST_PLUGINS"]
