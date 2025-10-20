"""Compatibility shim for historical ``pytest_bdd`` proxy imports.

The pytest-bdd plugin is registered dynamically through
``tests.pytest_plugin_registry``; this module remains so legacy imports do not
fail when pytest attempts to discover ``tests.behavior.steps._pytest_bdd_proxy``.
"""

__all__ = ("PYTEST_PLUGINS",)

# No plugins are exported directly from this module; see
# ``tests.pytest_plugin_registry`` for the canonical registry.
PYTEST_PLUGINS: tuple[str, ...] = ()
