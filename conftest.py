"""Root conftest.py to ensure pytest-bdd configuration is properly loaded."""

import importlib.util
import os

import pytest


def _setup_pytest_bdd() -> None:
    """Configure pytest-bdd if the plugin is available."""
    try:
        spec = importlib.util.find_spec("pytest_bdd.utils")
    except ModuleNotFoundError:
        spec = None
    if spec is None:
        return

    from pytest_bdd.utils import CONFIG_STACK  # local import

    @pytest.hookimpl(trylast=True)
    def pytest_configure(config):
        """Configure pytest-bdd and register custom markers."""
        config.addinivalue_line(
            "markers",
            "isolation: mark test to run in isolation due to interactions with other tests",
        )

        if not CONFIG_STACK:
            CONFIG_STACK.append(config)

        features_dir = os.path.join(
            os.path.dirname(__file__),
            "tests",
            "behavior",
            "features",
        )
        config.option.bdd_features_base_dir = features_dir
        config._inicache["bdd_features_base_dir"] = features_dir


_setup_pytest_bdd()
