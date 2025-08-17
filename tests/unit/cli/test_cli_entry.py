import runpy
from unittest.mock import patch

import click
import pytest
import typer
import typer.main

from devsynth.interface.ux_bridge import UXBridge


@pytest.fixture(autouse=True)
def patch_typer_types(monkeypatch):
    orig = typer.main.get_click_type

    def patched_get_click_type(*, annotation, parameter_info):
        if annotation in {UXBridge, typer.models.Context}:
            return click.STRING
        origin = getattr(annotation, "__origin__", None)
        if origin in {UXBridge, typer.models.Context}:
            return click.STRING
        return orig(annotation=annotation, parameter_info=parameter_info)

    monkeypatch.setattr(typer.main, "get_click_type", patched_get_click_type)


@pytest.mark.fast
def test_cli_entry_invokes_run_cli():
    """Ensure the CLI module calls run_cli when executed as __main__."""
    with patch("devsynth.adapters.cli.typer_adapter.run_cli") as mock_run:
        import sys

        orig = sys.argv
        sys.argv = ["devsynth"]

        try:
            runpy.run_module("devsynth.cli", run_name="__main__")
        except SystemExit:
            pass
        sys.argv = orig
        mock_run.assert_called_once()
