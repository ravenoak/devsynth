"""Additional run-tests CLI regression coverage for reporting guidance."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

import pytest
from typer.testing import CliRunner

from tests.unit.application.cli.commands.helpers import (
    SEGMENTATION_FAILURE_TIPS,
    build_minimal_cli_app,
)


@pytest.mark.fast
def test_cli_report_flag_warns_when_directory_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Successful runs with --report mention missing directories."""

    monkeypatch.chdir(tmp_path)

    # Provide minimal config loader stubs so CLI bootstraps cleanly.
    core_stub = ModuleType("devsynth.core.config_loader")
    core_stub.ConfigSearchResult = object  # type: ignore[attr-defined]
    core_stub.load_config = lambda *args, **kwargs: object()
    core_stub._find_project_config = lambda *args, **kwargs: None
    monkeypatch.setitem(sys.modules, "devsynth.core.config_loader", core_stub)

    tinydb_stub = ModuleType("tinydb")
    tinydb_stub.Query = object  # type: ignore[attr-defined]
    tinydb_stub.TinyDB = object  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "tinydb", tinydb_stub)

    for module_name, attr in [
        ("devsynth.application.cli.commands.edrr_cycle_cmd", "edrr_cycle_cmd"),
        ("devsynth.application.cli.commands.align_cmd", "align_cmd"),
        (
            "devsynth.application.cli.commands.analyze_manifest_cmd",
            "analyze_manifest_cmd",
        ),
        (
            "devsynth.application.cli.commands.generate_docs_cmd",
            "generate_docs_cmd",
        ),
        ("devsynth.application.cli.commands.ingest_cmd", "ingest_cmd"),
        ("devsynth.application.cli.commands.doctor_cmd", "doctor_cmd"),
        (
            "devsynth.application.cli.commands.validate_manifest_cmd",
            "validate_manifest_cmd",
        ),
        (
            "devsynth.application.cli.commands.validate_metadata_cmd",
            "validate_metadata_cmd",
        ),
    ]:
        stub_module = ModuleType(module_name)
        setattr(stub_module, attr, lambda *args, **kwargs: None)
        monkeypatch.setitem(sys.modules, module_name, stub_module)

    app, cli_module = build_minimal_cli_app(monkeypatch)

    runner = CliRunner()

    monkeypatch.setattr(cli_module, "run_tests", lambda *_, **__: (True, "pytest ok"))
    monkeypatch.setattr(
        cli_module, "_coverage_instrumentation_status", lambda: (True, None)
    )
    monkeypatch.setattr(cli_module, "coverage_artifacts_status", lambda: (True, None))
    monkeypatch.setattr(
        cli_module,
        "enforce_coverage_threshold",
        lambda exit_on_failure=False: 97.25,
    )

    emitted_bridges: list[object] = []
    monkeypatch.setattr(
        cli_module,
        "_emit_coverage_artifact_messages",
        lambda bridge: emitted_bridges.append(bridge),
    )

    monkeypatch.setattr(cli_module, "ensure_pytest_cov_plugin_env", lambda env: False)
    monkeypatch.setattr(cli_module, "ensure_pytest_bdd_plugin_env", lambda env: False)

    result = runner.invoke(app, ["--report"], prog_name="run-tests")

    assert result.exit_code == 0
    assert "Tests completed successfully" in result.stdout
    assert "Report flag was set but test_reports/ was not found" in result.stdout
    assert emitted_bridges, "artifact guidance should run when coverage succeeds"


@pytest.mark.fast
def test_cli_segment_option_failure_surfaces_failure_tips(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Segmentation failures bubble remediation guidance and exit non-zero."""

    monkeypatch.chdir(tmp_path)

    core_stub = ModuleType("devsynth.core.config_loader")
    core_stub.ConfigSearchResult = object  # type: ignore[attr-defined]
    core_stub.load_config = lambda *args, **kwargs: object()
    core_stub._find_project_config = lambda *args, **kwargs: None
    monkeypatch.setitem(sys.modules, "devsynth.core.config_loader", core_stub)
    tinydb_stub = ModuleType("tinydb")
    tinydb_stub.Query = object  # type: ignore[attr-defined]
    tinydb_stub.TinyDB = object  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "tinydb", tinydb_stub)

    for module_name, attr in [
        ("devsynth.application.cli.commands.edrr_cycle_cmd", "edrr_cycle_cmd"),
        ("devsynth.application.cli.commands.align_cmd", "align_cmd"),
        (
            "devsynth.application.cli.commands.analyze_manifest_cmd",
            "analyze_manifest_cmd",
        ),
        (
            "devsynth.application.cli.commands.generate_docs_cmd",
            "generate_docs_cmd",
        ),
        ("devsynth.application.cli.commands.ingest_cmd", "ingest_cmd"),
        ("devsynth.application.cli.commands.doctor_cmd", "doctor_cmd"),
        (
            "devsynth.application.cli.commands.validate_manifest_cmd",
            "validate_manifest_cmd",
        ),
        (
            "devsynth.application.cli.commands.validate_metadata_cmd",
            "validate_metadata_cmd",
        ),
    ]:
        stub_module = ModuleType(module_name)
        setattr(stub_module, attr, lambda *args, **kwargs: None)
        monkeypatch.setitem(sys.modules, module_name, stub_module)

    app, cli_module = build_minimal_cli_app(monkeypatch)

    captured_args: tuple[object, ...] = ()
    captured_kwargs: dict[str, object] = {}

    def failing_run_tests(*args: object, **kwargs: object) -> tuple[bool, str]:
        nonlocal captured_args
        captured_args = args
        captured_kwargs.update(kwargs)
        return False, "pytest failure output\n" + SEGMENTATION_FAILURE_TIPS

    monkeypatch.setattr(cli_module, "run_tests", failing_run_tests)
    monkeypatch.setattr(
        cli_module, "_coverage_instrumentation_status", lambda: (True, None)
    )
    monkeypatch.setattr(cli_module, "ensure_pytest_cov_plugin_env", lambda env: False)
    monkeypatch.setattr(cli_module, "ensure_pytest_bdd_plugin_env", lambda env: False)

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["--segment", "--segment-size", "7", "--speed", "fast"],
        prog_name="run-tests",
    )

    assert result.exit_code == 1
    assert "Tests failed" in result.stdout
    assert "pytest failure output" in result.stdout
    assert "Pytest exited with code 1" in result.stdout
    assert "Segment large suites" in result.stdout

    assert len(captured_args) >= 7
    assert captured_args[5] is True
    assert captured_args[6] == 7
