import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from devsynth.application.cli.commands.run_tests_cmd import run_tests_cmd
from tests.unit.application.cli.commands.helpers import build_minimal_cli_app


@pytest.mark.fast
def test_inventory_mode_writes_file_and_prints_message(monkeypatch, tmp_path, capsys):
    """ReqID: TR-CLI-03 — Inventory mode writes JSON and prints message.

    Validates that running with --inventory writes test_reports/test_inventory.json
    and prints a user-facing message with the path.
    """
    # run in temporary cwd
    monkeypatch.chdir(tmp_path)

    # Return deterministic collections
    def fake_collect(target: str, speed: str):  # noqa: ARG001
        return [f"{target}::{speed}::test_x"]

    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.setenv("DEVSYNTH_INNER_TEST", "1")
    monkeypatch.setenv("DEVSYNTH_TEST_ALLOW_REQUESTS", "true")

    monkeypatch.setattr(
        "devsynth.application.cli.commands.run_tests_cmd.collect_tests_with_cache",
        fake_collect,
    )

    run_tests_cmd(target="all-tests", inventory=True)  # programmatic call

    cout = capsys.readouterr().out
    assert "Test inventory exported to" in cout

    p = Path("test_reports/test_inventory.json")
    assert p.exists()
    data = json.loads(p.read_text())
    # basic structure sanity
    assert "generated_at" in data
    assert "targets" in data and isinstance(data["targets"], dict)


@pytest.mark.fast
def test_inventory_handles_collection_errors(monkeypatch, tmp_path):
    """ReqID: TR-CLI-04 — Inventory mode handles collection errors.

    When collection raises, ensure JSON still includes empty lists for all
        targets and speeds.
    """
    monkeypatch.chdir(tmp_path)

    def flaky_collect(target: str, speed: str):  # noqa: ARG001
        raise RuntimeError("boom")

    app, cli_module = build_minimal_cli_app(monkeypatch)
    monkeypatch.setattr(cli_module, "collect_tests_with_cache", flaky_collect)

    runner = CliRunner()
    result = runner.invoke(app, ["--inventory"], prog_name="run-tests")

    assert result.exception is None
    assert result.exit_code == 0
    assert "Test inventory exported to" in result.stdout

    p = Path("test_reports/test_inventory.json")
    assert p.exists()
    data = json.loads(p.read_text())
    # Ensure empty lists are used on exceptions
    expected_targets = {
        "all-tests",
        "unit-tests",
        "integration-tests",
        "behavior-tests",
    }
    expected_speeds = {"fast", "medium", "slow"}
    assert set(data["targets"].keys()) == expected_targets
    for tgt, speeds in data["targets"].items():
        assert set(speeds.keys()) == expected_speeds
        for spd, items in speeds.items():
            assert isinstance(items, list)
            assert items == []
