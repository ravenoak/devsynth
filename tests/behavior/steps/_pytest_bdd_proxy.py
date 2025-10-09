"""
Proxy module for pytest-bdd plugin to avoid import issues.

This module serves as a proxy to ensure pytest-bdd plugin can be loaded
without causing configuration errors during test discovery.
"""

# Re-export pytest-bdd plugin functionality
try:
    from pytest_bdd import plugin as pytest_bdd_plugin
except ImportError:
    # Fallback if pytest-bdd is not available
    pytest_bdd_plugin = None

# Expose the plugin for pytest discovery
pytest_plugins = ["pytest_bdd.plugin"] if pytest_bdd_plugin else []
