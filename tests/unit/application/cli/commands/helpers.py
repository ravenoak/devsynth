"""Shared utilities and canonical stubs for CLI runner tests.

This module centralizes lightweight replacements for the full CLI stack so
tests can exercise Typer integration without importing heavy dependencies.
Notably, ``SEGMENTATION_FAILURE_TIPS`` mirrors the remediation guidance that
``run-tests`` surfaces when segmented runs fail, keeping assertions aligned
with the production UX.
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Any

import click
import pytest
import typer.main as typer_main
from typer import Typer

SEGMENTATION_FAILURE_TIPS = (
    "Pytest exited with code 1\n"
    "- Segment large suites to localize failures\n"
    "- Re-run failing segments with --verbose for more detail"
)
"""Standard troubleshooting tips surfaced when segmented runs fail."""


def load_run_tests_cli_module(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Load ``run_tests_cmd`` with minimal registry stubs to avoid heavy deps."""

    original_get_click_type = typer_main.get_click_type

    def _patched_get_click_type(*, annotation, parameter_info):  # type: ignore[override]
        if annotation is object:
            return click.STRING
        return original_get_click_type(
            annotation=annotation, parameter_info=parameter_info
        )

    monkeypatch.setattr(typer_main, "get_click_type", _patched_get_click_type)

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

    provider_env_module = ModuleType("provider_env")

    class _ProviderEnv:
        def __init__(self, values: dict[str, str] | None = None) -> None:
            self._values = dict(values or {})

        @classmethod
        def from_env(cls) -> _ProviderEnv:
            return cls()

        def with_test_defaults(self) -> _ProviderEnv:
            return self

        def apply_to_env(self) -> None:
            return None

    provider_env_module.ProviderEnv = _ProviderEnv  # type: ignore[attr-defined]

    config_package = ModuleType("devsynth.config")
    config_package.provider_env = provider_env_module  # type: ignore[attr-defined]
    config_package.get_settings = lambda: {}  # type: ignore[attr-defined]
    config_package.get_project_config = lambda *args, **kwargs: None  # type: ignore[attr-defined]
    config_package.config_key_autocomplete = (  # type: ignore[attr-defined]
        lambda *_args, **_kwargs: []
    )
    settings_module = ModuleType("settings")
    settings_module.get_settings = lambda: {}  # type: ignore[attr-defined]
    settings_module.ensure_path_exists = lambda path: str(path)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "devsynth.config", config_package)
    monkeypatch.setitem(
        sys.modules,
        "devsynth.config.provider_env",
        provider_env_module,
    )
    monkeypatch.setitem(
        sys.modules,
        "devsynth.config.settings",
        settings_module,
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


__all__ = [
    "SEGMENTATION_FAILURE_TIPS",
    "build_minimal_cli_app",
    "load_run_tests_cli_module",
]
