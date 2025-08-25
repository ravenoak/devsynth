import click
import pytest

from devsynth.adapters.cli import typer_adapter as adapter


def _raiser(exc: Exception):
    def _inner(*args, **kwargs):  # noqa: ARG001
        raise exc

    return _inner


class TestExitCodes:
    @pytest.mark.medium
    def test_run_cli_runtime_error_exit_code_1(self, monkeypatch):
        # Make build_app return a callable that raises a generic Exception during execution
        monkeypatch.setattr(adapter, "build_app", lambda: _raiser(Exception("boom")))
        with pytest.raises(click.exceptions.Exit) as exc:
            adapter.run_cli()
        assert exc.value.exit_code == 1

    @pytest.mark.medium
    def test_run_cli_usage_error_exit_code_2(self, monkeypatch):
        monkeypatch.setattr(
            adapter, "build_app", lambda: _raiser(click.UsageError("bad args"))
        )
        with pytest.raises(click.exceptions.Exit) as exc:
            adapter.run_cli()
        assert exc.value.exit_code == 2

    @pytest.mark.medium
    def test_parse_args_runtime_error_exit_code_1(self, monkeypatch):
        monkeypatch.setattr(adapter, "build_app", lambda: _raiser(Exception("oops")))
        with pytest.raises(click.exceptions.Exit) as exc:
            adapter.parse_args(["--version"])  # args ignored by our stub
        assert exc.value.exit_code == 1

    @pytest.mark.medium
    def test_parse_args_usage_error_exit_code_2(self, monkeypatch):
        monkeypatch.setattr(
            adapter, "build_app", lambda: _raiser(click.BadParameter("param"))
        )
        with pytest.raises(click.exceptions.Exit) as exc:
            adapter.parse_args(["--unknown"])  # args ignored by our stub
        assert exc.value.exit_code == 2
