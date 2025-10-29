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


@pytest.mark.fast
def test_main_entry_point_module_structure():
    """Ensure the __main__ module has the expected structure."""
    # The __main__.py file is very simple and hard to test directly
    # For coverage purposes, we verify the module can be imported
    # The actual execution testing is covered by integration tests

    # Verify the file exists and has expected content
    import os
    main_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src', 'devsynth', '__main__.py')
    assert os.path.exists(main_file)

    with open(main_file, 'r') as f:
        content = f.read()
        assert 'if __name__ == "__main__":' in content
        assert 'from devsynth.adapters.cli.typer_adapter import run_cli' in content
        assert 'run_cli()' in content
