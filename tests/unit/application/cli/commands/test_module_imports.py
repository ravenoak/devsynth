"""Ensure CLI command modules import successfully."""

from __future__ import annotations

import importlib
import pkgutil

import pytest

import devsynth.application.cli.commands as commands_pkg

MODULE_NAMES = sorted(
    [
        module.name
        for module in pkgutil.iter_modules(
            commands_pkg.__path__, commands_pkg.__name__ + "."
        )
    ]
)


@pytest.mark.parametrize("module_name", MODULE_NAMES)
def test_command_module_import(module_name: str) -> None:
    """Each CLI command module should be importable."""

    importlib.import_module(module_name)
