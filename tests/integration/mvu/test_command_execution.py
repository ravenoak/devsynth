import pytest
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import build_app

pytestmark = pytest.mark.fast


def test_mvu_exec_runs_command():
    runner = CliRunner()
    app = build_app()
    result = runner.invoke(app, ["mvu", "exec", "echo", "hello"])
    assert result.exit_code == 0
    assert "hello" in result.output


def test_mvu_exec_propagates_error(tmp_path):
    script = tmp_path / "fail.sh"
    script.write_text("#!/bin/bash\necho err >&2\nexit 3\n")
    script.chmod(0o755)
    runner = CliRunner()
    app = build_app()
    result = runner.invoke(app, ["mvu", "exec", str(script)])
    assert result.exit_code == 3
    assert "err" in result.output
