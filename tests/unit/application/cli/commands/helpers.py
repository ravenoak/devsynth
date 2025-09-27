"""Shared utilities for CLI runner tests."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Any

import pytest
from typer import Typer


def load_run_tests_cli_module(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Load ``run_tests_cmd`` with minimal registry stubs to avoid heavy deps."""

    alignment_module = ModuleType("alignment_metrics_cmd")

    def _noop_alignment(*args: Any, **kwargs: Any) -> bool:
        return True

    alignment_module.alignment_metrics_cmd = _noop_alignment  # type: ignore[attr-defined]
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.alignment_metrics_cmd",
        alignment_module,
    )

    test_metrics_module = ModuleType("test_metrics_cmd")
    test_metrics_module.test_metrics_cmd = _noop_alignment  # type: ignore[attr-defined]
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.test_metrics_cmd",
        test_metrics_module,
    )

    registry_module = ModuleType("registry")

    class _Registry(dict):
        def __getitem__(self, key: str) -> Any:  # type: ignore[override]
            if key not in self:
                super().__setitem__(key, _noop_alignment)
            return super().__getitem__(key)

    registry_module.COMMAND_REGISTRY = _Registry(
        {
            "alignment-metrics": alignment_module.alignment_metrics_cmd,
            "test-metrics": test_metrics_module.test_metrics_cmd,
        }
    )

    def _register(name: str, fn: Any) -> None:
        registry_module.COMMAND_REGISTRY[name] = fn

    registry_module.register = _register  # type: ignore[attr-defined]
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.registry",
        registry_module,
    )

    for module_name in [
        "devsynth.application.cli",
        "devsynth.application.cli.cli_commands",
        "devsynth.application.cli.commands.metrics_cmds",
        "devsynth.application.cli.commands.run_tests_cmd",
    ]:
        sys.modules.pop(module_name, None)

    return importlib.import_module("devsynth.application.cli.commands.run_tests_cmd")


def build_minimal_cli_app(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Typer, ModuleType]:
    """Construct a Typer app exposing only the ``run-tests`` command."""

    cli_module = load_run_tests_cli_module(monkeypatch)
    app = Typer()
    app.command(name="run-tests")(cli_module.run_tests_cmd)
    return app, cli_module


__all__ = ["build_minimal_cli_app", "load_run_tests_cli_module"]
