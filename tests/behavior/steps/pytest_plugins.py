"""Backward-compatible stub for behavior-level pytest plugin discovery.

Plugin registration now occurs in ``tests/conftest.py`` via the centralized
registry under ``tests.pytest_plugin_registry``. This module remains so pytest
can continue importing ``tests.behavior.steps.pytest_plugins`` without
re-registering plugins or raising import errors during collection.
"""

# The module intentionally exposes no ``pytest_plugins`` attribute.
