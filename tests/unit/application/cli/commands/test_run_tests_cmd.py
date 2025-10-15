# flake8: noqa: E501
import os
from pathlib import Path
from typing import Any

import pytest
import typer

import devsynth.application.cli.commands.run_tests_cmd as run_tests_cmd_module
from devsynth.application.cli.commands.run_tests_cmd import run_tests_cmd
from devsynth.interface.ux_bridge import UXBridge


class DummyBridge(UXBridge):
    def __init__(self) -> None:
        self.messages: list[str] = []

    # Implement abstract methods minimally for tests
    def ask_question(self, message: str, *, choices=None, default=None, show_default=True) -> str:  # type: ignore[override]
        return default or ""

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:  # type: ignore[override]
        return default

    def display_result(self, message: str, *, highlight: bool = False, message_type: str | None = None) -> None:  # type: ignore[override]
        self.messages.append(message)


@pytest.fixture(autouse=True)
def _patch_coverage_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure coverage enforcement is treated as passing in CLI tests."""

    monkeypatch.setattr(
        "devsynth.testing.run_tests.enforce_coverage_threshold",
        lambda *args, **kwargs: 100.0,
    )
    monkeypatch.setattr(
        "devsynth.testing.run_tests.coverage_artifacts_status",
        lambda: (True, None),
    )
    monkeypatch.setattr(
        "devsynth.testing.run_tests.pytest_cov_support_status",
        lambda env=None: (True, None),
    )


@pytest.mark.fast
def test_allows_requests_env_default_for_unit(monkeypatch, tmp_path) -> None:
    """ReqID: CLI-RT-14 — unit-tests default allows requests when unset."""
    calls: dict[str, Any] = {}

    def fake_run_tests(*args, **kwargs) -> tuple[bool, str]:
        calls["args"] = args
        calls["kwargs"] = kwargs
        return True, "OK"

    # Ensure env var is not pre-set
    if "DEVSYNTH_TEST_ALLOW_REQUESTS" in os.environ:
        monkeypatch.delenv("DEVSYNTH_TEST_ALLOW_REQUESTS", raising=False)
    # Also remove plugin disable to allow default path in command
    if "PYTEST_DISABLE_PLUGIN_AUTOLOAD" in os.environ:
        monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)

    monkeypatch.setattr(
        "devsynth.testing.run_tests.run_tests", fake_run_tests
    )
    bridge = DummyBridge()

    run_tests_cmd(
        target="unit-tests",
        speeds=[],
        report=False,
        verbose=False,
        no_parallel=False,
        smoke=False,
        segment=False,
        segment_size=50,
        maxfail=None,
        features=[],
        inventory=False,
        marker=None,
        bridge=bridge,
    )

    assert os.environ.get("DEVSYNTH_TEST_ALLOW_REQUESTS") == "true"
    # Ensure CLI emitted a success message
    assert any("Tests completed successfully" in m for m in bridge.messages)


@pytest.mark.fast
def test_smoke_mode_sets_env_and_disables_parallel(monkeypatch, tmp_path) -> None:
    """ReqID: CLI-RT-02 — Smoke mode enforces env and disables parallel."""
    calls: dict[str, Any] = {}

    def fake_run_tests(*args, **kwargs) -> tuple[bool, str]:
        # Capture invocation for assertions
        calls["args"] = args
        calls["kwargs"] = kwargs
        return True, "OK"

    # Ensure a clean start without pre-set pytest plugin envs
    if "PYTEST_DISABLE_PLUGIN_AUTOLOAD" in os.environ:
        monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)
    if "PYTEST_ADDOPTS" in os.environ:
        monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)

    monkeypatch.setenv("HOME", str(tmp_path))  # avoid odd env interactions
    monkeypatch.setattr(
        "devsynth.testing.run_tests.run_tests", fake_run_tests
    )

    bridge = DummyBridge()

    run_tests_cmd(
        target="unit-tests",
        speeds=[],
        report=False,
        verbose=False,
        no_parallel=False,
        smoke=True,
        segment=False,
        segment_size=50,
        maxfail=None,
        features=[],
        inventory=False,
        marker=None,
        bridge=bridge,
    )

    # In smoke mode
    assert os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"
    assert "-p no:xdist" in os.environ.get("PYTEST_ADDOPTS", "")
    # no_parallel must be forced True so run_tests is called with parallel=False
    assert calls["args"][4] is False  # parallel parameter
    # Message flow
    assert any("Tests completed successfully" in m for m in bridge.messages)


@pytest.mark.fast
def test_feature_flag_mapping_sets_env(monkeypatch) -> None:
    """ReqID: CLI-RT-04 — --feature flags map to DEVSYNTH_FEATURE_* env vars."""

    def fake_run_tests(*args, **kwargs) -> tuple[bool, str]:
        return True, ""

    monkeypatch.setattr(
        "devsynth.testing.run_tests.run_tests", fake_run_tests
    )

    bridge = DummyBridge()

    run_tests_cmd(
        target="unit-tests",
        speeds=["fast"],
        features=["awesome", "beta=false"],
        bridge=bridge,
    )

    assert os.environ.get("DEVSYNTH_FEATURE_AWESOME") == "true"
    assert os.environ.get("DEVSYNTH_FEATURE_BETA") == "false"


@pytest.mark.fast
def test_marker_passthrough(monkeypatch) -> None:
    """ReqID: CLI-RT-11 — --marker passes through to extra_marker."""
    captured = {}

    def fake_run_tests(*args, **kwargs) -> tuple[bool, str]:
        captured.update(kwargs)
        return True, ""

    monkeypatch.setattr(
        "devsynth.testing.run_tests.run_tests", fake_run_tests
    )

    bridge = DummyBridge()

    run_tests_cmd(
        target="unit-tests",
        speeds=["fast"],
        marker="requires_resource('lmstudio')",
        bridge=bridge,
    )

    assert captured.get("extra_marker") == "requires_resource('lmstudio')"


@pytest.mark.fast
def test_inventory_exports_file(monkeypatch, tmp_path, tmp_path_factory) -> None:
    """ReqID: CLI-RT-08 — inventory mode exports JSON and skips run."""

    # Return deterministic collections
    def fake_collect(tgt: str, spd: str | None = None) -> list[str]:
        return ["tests/unit/test_example.py::test_ok"]

    def fake_run_tests(*args, **kwargs) -> tuple[bool, str]:
        pytest.fail("run_tests should not be called in inventory mode")

    monkeypatch.setattr(
        "devsynth.application.cli.commands.run_tests_cmd.collect_tests_with_cache",
        fake_collect,
    )
    monkeypatch.setattr(
        "devsynth.testing.run_tests.run_tests", fake_run_tests
    )

    bridge = DummyBridge()

    # Ensure we operate in an isolated working directory
    cwd = tmp_path
    os.chdir(cwd)
    try:
        run_tests_cmd(target="all-tests", inventory=True, bridge=bridge)
        out = Path("test_reports").glob("**/test_inventory.json")
        paths = list(out)
        assert paths, "inventory file not created"
        content = paths[0].read_text()
        assert "generated_at" in content and "targets" in content
        # UX message communicated
        assert any("Test inventory exported" in m for m in bridge.messages)
    finally:
        pass


@pytest.mark.fast
def test_integration_target_retains_cov_when_no_report(monkeypatch) -> None:
    """ReqID: CLI-RT-03 — Integration target without report keeps coverage active."""
    # Ensure PYTEST_ADDOPTS starts clean
    if "PYTEST_ADDOPTS" in os.environ:
        monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)

    def fake_run_tests(*args, **kwargs) -> tuple[bool, str]:
        return True, ""

    monkeypatch.setattr(
        "devsynth.testing.run_tests.run_tests", fake_run_tests
    )
    bridge = DummyBridge()

    run_tests_cmd(
        target="integration-tests",
        speeds=["fast"],
        report=False,
        verbose=False,
        no_parallel=True,
        smoke=False,
        segment=False,
        segment_size=50,
        maxfail=None,
        features=[],
        inventory=False,
        marker=None,
        bridge=bridge,
    )

    assert "-p no:cov" not in os.environ.get("PYTEST_ADDOPTS", "")
    assert any("Coverage" in message for message in bridge.messages)


@pytest.mark.fast
def test_invalid_target_prints_error_and_exits(monkeypatch) -> None:
    """ReqID: CLI-RT-05 — invalid --target exits with code 2 and prints error."""
    bridge = DummyBridge()
    with pytest.raises(typer.Exit) as ei:
        run_tests_cmd(target="bogus", bridge=bridge)
    assert ei.value.exit_code == 2
    # Expect an error message about allowed targets
    assert any("Invalid --target value" in m for m in bridge.messages)


@pytest.mark.fast
def test_invalid_speed_prints_error_and_exits(monkeypatch) -> None:
    """ReqID: CLI-RT-07 — invalid --speed exits with code 2 and prints error."""
    bridge = DummyBridge()
    with pytest.raises(typer.Exit) as ei:
        run_tests_cmd(target="unit-tests", speeds=["warp"], bridge=bridge)
    assert ei.value.exit_code == 2
    assert any("Invalid --speed value" in m for m in bridge.messages)


@pytest.mark.fast
def test_inner_test_env_disables_plugins_and_parallel(monkeypatch) -> None:
    """ReqID: CLI-RT-09 — DEVSYNTH_INNER_TEST disables plugins and parallel."""
    # Start with a clean env
    if "PYTEST_ADDOPTS" in os.environ:
        monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)
    if "PYTEST_DISABLE_PLUGIN_AUTOLOAD" in os.environ:
        monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)

    # Signal inner test mode
    monkeypatch.setenv("DEVSYNTH_INNER_TEST", "1")

    captured: dict[str, Any] = {}

    def fake_run_tests(*args, **kwargs):  # noqa: ANN001
        # Capture positional args to assert parallel flag (index 4)
        captured["args"] = args
        captured["kwargs"] = kwargs
        return True, "OK"

    monkeypatch.setattr(
        "devsynth.testing.run_tests.run_tests", fake_run_tests
    )

    bridge = DummyBridge()

    run_tests_cmd(
        target="unit-tests",
        speeds=["fast"],
        report=False,
        verbose=False,
        no_parallel=False,  # should be overridden by inner test handling
        smoke=False,
        segment=False,
        segment_size=50,
        maxfail=None,
        features=[],
        inventory=False,
        marker=None,
        bridge=bridge,
    )

    # Env flags should be applied for inner test optimization
    assert os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"
    addopts = os.environ.get("PYTEST_ADDOPTS", "")
    assert "-p no:xdist" in addopts and "-p no:cov" not in addopts
    # parallel arg passed into run_tests should be False (index 4)
    assert captured["args"][4] is False
    assert any("Tests completed successfully" in m for m in bridge.messages)


@pytest.mark.fast
def test_verbose_and_fast_timeout_env_behavior(monkeypatch) -> None:
    """ReqID: CLI-RT-10 — fast-only timeout defaults to 120s and verbose passes through."""
    # Ensure timeout var is unset to observe defaulting behavior
    if "DEVSYNTH_TEST_TIMEOUT_SECONDS" in os.environ:
        monkeypatch.delenv("DEVSYNTH_TEST_TIMEOUT_SECONDS", raising=False)

    def fake_run_tests(*args, **kwargs):  # noqa: ANN001
        # verbose should be True (positional index 2)
        assert args[2] is True
        return True, ""

    monkeypatch.setattr(
        "devsynth.testing.run_tests.run_tests", fake_run_tests
    )

    bridge = DummyBridge()

    run_tests_cmd(
        target="unit-tests",
        speeds=["fast"],  # fast-only path (non-smoke) should set 120s timeout
        report=False,
        verbose=True,
        no_parallel=True,
        smoke=False,
        segment=False,
        segment_size=50,
        maxfail=None,
        features=[],
        inventory=False,
        marker=None,
        bridge=bridge,
    )

    assert os.environ.get("DEVSYNTH_TEST_TIMEOUT_SECONDS") == "120"
    assert any("Tests completed successfully" in m for m in bridge.messages)


@pytest.mark.fast
def test_report_mode_prints_report_path_message(monkeypatch, tmp_path) -> None:
    """ReqID: CLI-RT-16 — --report prints friendly test_reports/ path pointer."""
    # Ensure a clean working directory and create test_reports/ so CLI emits the green path message
    cwd = tmp_path
    os.chdir(cwd)
    (tmp_path / "test_reports").mkdir(parents=True, exist_ok=True)

    def fake_run_tests(*args, **kwargs):  # noqa: ANN001
        return True, ""

    monkeypatch.setattr(
        "devsynth.testing.run_tests.run_tests", fake_run_tests
    )

    bridge = DummyBridge()

    run_tests_cmd(
        target="unit-tests",
        speeds=["fast"],
        report=True,
        verbose=False,
        no_parallel=True,
        smoke=False,
        segment=False,
        segment_size=50,
        maxfail=None,
        features=[],
        inventory=False,
        marker=None,
        bridge=bridge,
    )

    # Should include success message and the HTML report path pointer
    assert any("Tests completed successfully" in m for m in bridge.messages)
    assert any("HTML report available under" in m for m in bridge.messages)


@pytest.mark.fast
def test_failed_run_surfaces_maxfail_guidance(monkeypatch) -> None:
    """ReqID: CLI-RT-17 — Failed runs surface maxfail troubleshooting tips."""

    failure_output = (
        "Pytest exited with code 1. Command: python -m pytest --maxfail=2 tests/unit\n"
        "Troubleshooting tips:\n"
        "- Segment large suites to localize failures.\n"
    )

    def fake_run_tests(*args, **kwargs) -> tuple[bool, str]:  # noqa: ANN001
        return False, failure_output

    monkeypatch.setattr(
        "devsynth.application.cli.commands.run_tests_cmd.run_tests",
        fake_run_tests,
    )

    bridge = DummyBridge()

    with pytest.raises(typer.Exit) as excinfo:
        run_tests_cmd(
            target="unit-tests",
            speeds=["fast"],
            report=False,
            verbose=False,
            no_parallel=True,
            smoke=False,
            segment=True,
            segment_size=5,
            maxfail=2,
            features=[],
            inventory=False,
            marker=None,
            bridge=bridge,
        )

    assert excinfo.value.exit_code == 1
    assert any("Tests failed" in msg for msg in bridge.messages)
    assert any("--maxfail=2" in msg for msg in bridge.messages)
    assert any("Pytest exited with code 1" in msg for msg in bridge.messages)


@pytest.mark.fast
def test_run_tests_cmd_exits_when_pytest_cov_missing(monkeypatch) -> None:
    """Missing pytest-cov triggers an actionable remediation banner."""

    monkeypatch.setattr(
        "devsynth.application.cli.commands.run_tests_cmd.pytest_cov_support_status",
        lambda env=None: (
            False,
            run_tests_cmd_module.PYTEST_COV_PLUGIN_MISSING_MESSAGE,
        ),
    )

    def _fail_run_tests(*args: object, **kwargs: object) -> tuple[bool, str]:
        raise AssertionError("run_tests should not execute when pytest-cov is missing")

    monkeypatch.setattr(
        "devsynth.application.cli.commands.run_tests_cmd.run_tests",
        _fail_run_tests,
    )

    bridge = DummyBridge()

    with pytest.raises(typer.Exit) as excinfo:
        run_tests_cmd(
            target="unit-tests",
            speeds=[],
            report=False,
            verbose=False,
            no_parallel=False,
            smoke=False,
            segment=False,
            segment_size=50,
            maxfail=None,
            features=[],
            inventory=False,
            marker=None,
            bridge=bridge,
        )

    assert excinfo.value.code == 1
    assert any(
        run_tests_cmd_module.PYTEST_COV_PLUGIN_MISSING_MESSAGE in msg
        for msg in bridge.messages
    )


@pytest.mark.fast
def test_run_tests_cmd_exits_when_autoload_blocks_pytest_cov(monkeypatch) -> None:
    """Autoload blocking pytest-cov halts execution for standard runs."""

    monkeypatch.setattr(
        "devsynth.application.cli.commands.run_tests_cmd.pytest_cov_support_status",
        lambda env=None: (
            False,
            run_tests_cmd_module.PYTEST_COV_AUTOLOAD_DISABLED_MESSAGE,
        ),
    )

    def _fail_run_tests(*args: object, **kwargs: object) -> tuple[bool, str]:
        raise AssertionError("run_tests should not execute when pytest-cov is disabled")

    monkeypatch.setattr(
        "devsynth.application.cli.commands.run_tests_cmd.run_tests",
        _fail_run_tests,
    )

    bridge = DummyBridge()

    with pytest.raises(typer.Exit) as excinfo:
        run_tests_cmd(
            target="unit-tests",
            speeds=[],
            report=False,
            verbose=False,
            no_parallel=False,
            smoke=False,
            segment=False,
            segment_size=50,
            maxfail=None,
            features=[],
            inventory=False,
            marker=None,
            bridge=bridge,
        )

    assert excinfo.value.code == 1
    assert any(
        run_tests_cmd_module.PYTEST_COV_AUTOLOAD_DISABLED_MESSAGE in msg
        for msg in bridge.messages
    )
