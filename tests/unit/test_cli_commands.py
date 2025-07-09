import click
import typer
import typer.main
from typer.testing import CliRunner
import pytest
from devsynth.adapters.cli.typer_adapter import build_app
from devsynth.interface.ux_bridge import UXBridge


@pytest.fixture(autouse=True)
def patch_typer_types(monkeypatch):
    orig = typer.main.get_click_type

    def patched_get_click_type(*, annotation, parameter_info):
        if annotation in {UXBridge, typer.models.Context}:
            return click.STRING
        origin = getattr(annotation, '__origin__', None)
        if origin in {UXBridge, typer.models.Context
            } or annotation is dict or origin is dict:
            return click.STRING
        return orig(annotation=annotation, parameter_info=parameter_info)
    monkeypatch.setattr(typer.main, 'get_click_type', patched_get_click_type)


class TestCLIHelpOutput:
    """Tests for the CLIHelpOutput component.

ReqID: N/A"""
    runner = CliRunner()

    def test_help_lists_commands_succeeds(self):
        """Test that help lists commands succeeds.

ReqID: N/A"""
        app = build_app()
        result = self.runner.invoke(app, ['--help'])
        assert result.exit_code == 0
        expected = ['init', 'spec', 'test', 'code', 'run-pipeline',
            'config', 'inspect', 'gather', 'webapp', 'webui', 'dbschema',
            'doctor', 'check', 'refactor', 'inspect-code', 'edrr-cycle',
            'align', 'alignment-metrics', 'inspect-config',
            'validate-manifest', 'validate-metadata', 'test-metrics',
            'generate-docs', 'ingest', 'apispec', 'serve']
        for cmd in expected:
            assert cmd in result.output

    def test_help_omits_deprecated_aliases_succeeds(self):
        """Test that help omits deprecated aliases succeeds.

ReqID: N/A"""
        app = build_app()
        result = self.runner.invoke(app, ['--help'])
        assert result.exit_code == 0
        lines = [line.strip() for line in result.output.splitlines()]
        assert all(not line.startswith('adaptive') for line in lines)
        assert all(not line.startswith('analyze ') for line in lines)
