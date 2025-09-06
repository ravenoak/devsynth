import os
from typing import Any, Tuple

import pytest

# Target under test
import devsynth.application.cli.commands.run_tests_cmd as rtc


class StubBridge:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def print(self, msg: str) -> None:
        # Collect messages for assertions if needed
        self.messages.append(str(msg))


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch):
    # Ensure a clean slate for env vars we mutate
    keys = [
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
        "PYTEST_ADDOPTS",
        "DEVSYNTH_TEST_TIMEOUT_SECONDS",
        "DEVSYNTH_INNER_TEST",
        "DEVSYNTH_TEST_ALLOW_REQUESTS",
        "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE",
        "DEVSYNTH_FEATURE_EXPA",
        "DEVSYNTH_FEATURE_FEATURE_B",
    ]
    for k in keys:
        monkeypatch.delenv(k, raising=False)
    yield
    for k in keys:
        monkeypatch.delenv(k, raising=False)


@pytest.mark.fast
@pytest.mark.isolation
def test_parse_feature_options_basic():
    """ReqID: CLI-RT-01 — Parse --feature options into env flags."""
    result = rtc._parse_feature_options(
        ["expA", "feature_b=false", "zzz=0", "yup=yes"]
    )  # noqa: SLF001
    assert result == {
        "expA": True,
        "feature_b": False,
        "zzz": False,
        "yup": True,
    }


@pytest.mark.fast
@pytest.mark.isolation
def test_smoke_mode_enforces_env_and_no_parallel(monkeypatch: pytest.MonkeyPatch):
    """ReqID: CLI-RT-02 — Smoke mode enforces env and disables parallel."""
    # Arrange
    stub = StubBridge()
    monkeypatch.setattr(rtc, "bridge", stub, raising=False)

    captured: dict[str, Any] = {}

    def fake_run_tests(
        target: str,
        speed_categories: Any,
        verbose: bool,
        report: bool,
        parallel: bool,
        segment: bool,
        segment_size: int,
        maxfail: int | None,
        **kwargs: Any,
    ) -> tuple[bool, str]:
        captured.update(
            dict(
                target=target,
                speed_categories=speed_categories,
                verbose=verbose,
                report=report,
                parallel=parallel,
                segment=segment,
                segment_size=segment_size,
                maxfail=maxfail,
                kwargs=kwargs,
            )
        )
        return True, "ok"

    monkeypatch.setattr(rtc, "run_tests", fake_run_tests)

    # Act
    rtc.run_tests_cmd(
        target="unit-tests",
        speeds=[],  # ensure defaulting in smoke
        smoke=True,
        no_parallel=False,  # explicit False should still be forced to True then flipped to parallel=False
        report=False,
        verbose=False,
        segment=False,
        segment_size=50,
        maxfail=None,
    )

    # Assert environment effects
    assert os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"
    assert "-p no:xdist" in os.environ.get("PYTEST_ADDOPTS", "")
    assert "-p no:cov" in os.environ.get("PYTEST_ADDOPTS", "")
    assert os.environ.get("DEVSYNTH_TEST_TIMEOUT_SECONDS") == "30"

    # Assert call args
    assert captured["target"] == "unit-tests"
    # Default speed in smoke should be fast when not provided
    assert captured["speed_categories"] == ["fast"]
    # no_parallel gets forced True; function passes parallel = not no_parallel
    assert captured["parallel"] is False


@pytest.mark.fast
@pytest.mark.isolation
def test_integration_without_report_adds_no_cov(monkeypatch: pytest.MonkeyPatch):
    """ReqID: CLI-RT-03 — Integration target without report disables coverage plugin."""
    stub = StubBridge()
    monkeypatch.setattr(rtc, "bridge", stub, raising=False)

    # Pre-set unrelated addopts to ensure we append
    os.environ["PYTEST_ADDOPTS"] = "-q"

    def fake_run_tests(*args: Any, **kwargs: Any) -> tuple[bool, str]:
        return True, "ok"

    monkeypatch.setattr(rtc, "run_tests", fake_run_tests)

    rtc.run_tests_cmd(target="integration-tests", report=False, smoke=False, speeds=["fast"])  # type: ignore[arg-type]

    assert "-p no:cov" in os.environ.get("PYTEST_ADDOPTS", "")


@pytest.mark.fast
@pytest.mark.isolation
def test_feature_flags_mapping(monkeypatch: pytest.MonkeyPatch):
    """ReqID: CLI-RT-04 — --feature flag mapping sets DEVSYNTH_FEATURE_* env vars."""
    stub = StubBridge()
    monkeypatch.setattr(rtc, "bridge", stub, raising=False)

    def fake_run_tests(*args: Any, **kwargs: Any) -> tuple[bool, str]:
        return True, "ok"

    monkeypatch.setattr(rtc, "run_tests", fake_run_tests)

    rtc.run_tests_cmd(target="all-tests", smoke=False, report=False, features=["expA", "feature_b=false"])  # type: ignore[arg-type]

    assert os.environ.get("DEVSYNTH_FEATURE_EXPA") == "true"
    assert os.environ.get("DEVSYNTH_FEATURE_FEATURE_B") == "false"


@pytest.mark.fast
@pytest.mark.isolation
def test_invalid_target_exits_with_code_2(monkeypatch: pytest.MonkeyPatch):
    """ReqID: CLI-RT-05 — Invalid --target exits with code 2."""
    import click

    stub = StubBridge()
    monkeypatch.setattr(rtc, "bridge", stub, raising=False)

    with pytest.raises((SystemExit, click.exceptions.Exit)) as excinfo:  # type: ignore[attr-defined]
        rtc.run_tests_cmd(target="not-a-target", smoke=False)  # type: ignore[arg-type]
    # Typer/Typer->Click Exit may expose code or exit_code
    val = excinfo.value
    code = getattr(val, "code", getattr(val, "exit_code", None))
    assert code == 2


@pytest.mark.fast
@pytest.mark.isolation
def test_no_parallel_disables_parallel(monkeypatch: pytest.MonkeyPatch):
    """ReqID: CLI-RT-06 — --no-parallel results in parallel=False passed to runner (non-smoke)."""
    stub = StubBridge()
    monkeypatch.setattr(rtc, "bridge", stub, raising=False)

    captured: dict[str, Any] = {}

    def fake_run_tests(
        target: str,
        speed_categories: Any,
        verbose: bool,
        report: bool,
        parallel: bool,
        segment: bool,
        segment_size: int,
        maxfail: int | None,
        **kwargs: Any,
    ) -> tuple[bool, str]:
        captured.update(dict(parallel=parallel, target=target, speed_categories=speed_categories))
        return True, "ok"

    monkeypatch.setattr(rtc, "run_tests", fake_run_tests)

    rtc.run_tests_cmd(
        target="unit-tests",
        speeds=["fast"],  # explicit speed, not smoke
        smoke=False,
        no_parallel=True,
        report=False,
        verbose=False,
        segment=False,
        segment_size=50,
        maxfail=None,
    )

    assert captured.get("parallel") is False


@pytest.mark.fast
@pytest.mark.isolation
def test_invalid_speed_exits_with_code_2(monkeypatch: pytest.MonkeyPatch):
    """ReqID: CLI-RT-07 — Invalid --speed exits with code 2 and prints message."""
    import click

    stub = StubBridge()
    monkeypatch.setattr(rtc, "bridge", stub, raising=False)

    with pytest.raises((SystemExit, click.exceptions.Exit)) as excinfo:  # type: ignore[attr-defined]
        rtc.run_tests_cmd(target="unit-tests", speeds=["fast", "warp"], smoke=False)  # type: ignore[arg-type]
    val = excinfo.value
    code = getattr(val, "code", getattr(val, "exit_code", None))
    assert code == 2
    assert any("Invalid --speed" in m for m in stub.messages)


@pytest.mark.fast
@pytest.mark.isolation
def test_inventory_mode_exports_and_skips_run(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """ReqID: CLI-RT-08 — Inventory exports file and returns without running tests."""
    stub = StubBridge()
    monkeypatch.setattr(rtc, "bridge", stub, raising=False)

    # Ensure we don't call run_tests
    def fail_run_tests(*args: Any, **kwargs: Any):  # pragma: no cover - should not be invoked
        raise AssertionError("run_tests should not be called in inventory mode")

    monkeypatch.setattr(rtc, "run_tests", fail_run_tests)

    # Mock collect to return deterministic small lists
    monkeypatch.setattr(rtc, "collect_tests_with_cache", lambda t, s: [f"{t}:{s}:test_a"])  # type: ignore[misc]

    # Run inventory mode
    rtc.run_tests_cmd(target="all-tests", inventory=True)  # type: ignore[arg-type]

    # Validate output path and message
    out = tmp_path / "dummy"
    # Report defaults to test_reports/test_inventory.json
    assert any("Test inventory exported to" in m for m in stub.messages)


@pytest.mark.fast
@pytest.mark.isolation
def test_inner_test_env_disables_plugins_and_parallel(monkeypatch: pytest.MonkeyPatch):
    """ReqID: CLI-RT-09 — DEVSYNTH_INNER_TEST enforces plugin disable and no parallel."""
    stub = StubBridge()
    monkeypatch.setattr(rtc, "bridge", stub, raising=False)

    monkeypatch.setenv("DEVSYNTH_INNER_TEST", "1")

    captured: dict[str, Any] = {}

    def fake_run_tests(
        target: str,
        speed_categories: Any,
        verbose: bool,
        report: bool,
        parallel: bool,
        segment: bool,
        segment_size: int,
        maxfail: int | None,
        **kwargs: Any,
    ) -> tuple[bool, str]:
        captured.update(dict(parallel=parallel))
        return True, "ok"

    monkeypatch.setattr(rtc, "run_tests", fake_run_tests)

    rtc.run_tests_cmd(target="unit-tests", smoke=False, speeds=["fast"])  # type: ignore[arg-type]

    assert os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"
    assert "-p no:xdist" in os.environ.get("PYTEST_ADDOPTS", "")
    assert captured.get("parallel") is False


@pytest.mark.fast
@pytest.mark.isolation
def test_fast_only_timeout_non_smoke_sets_120(monkeypatch: pytest.MonkeyPatch):
    """ReqID: CLI-RT-10 — Fast-only non-smoke sets timeout 120 seconds."""
    stub = StubBridge()
    monkeypatch.setattr(rtc, "bridge", stub, raising=False)

    def fake_run_tests(*args: Any, **kwargs: Any) -> tuple[bool, str]:
        return True, "ok"

    monkeypatch.setattr(rtc, "run_tests", fake_run_tests)

    rtc.run_tests_cmd(target="unit-tests", speeds=["fast"], smoke=False)  # type: ignore[arg-type]

    assert os.environ.get("DEVSYNTH_TEST_TIMEOUT_SECONDS") == "120"


@pytest.mark.fast
@pytest.mark.isolation
def test_marker_passthrough_to_extra_marker(monkeypatch: pytest.MonkeyPatch):
    """ReqID: CLI-RT-11 — --marker passes through as extra_marker to run_tests."""
    stub = StubBridge()
    monkeypatch.setattr(rtc, "bridge", stub, raising=False)

    captured: dict[str, Any] = {}

    def fake_run_tests(*args: Any, **kwargs: Any) -> tuple[bool, str]:
        captured.update(kwargs)
        return True, "ok"

    monkeypatch.setattr(rtc, "run_tests", fake_run_tests)

    rtc.run_tests_cmd(target="unit-tests", marker="requires_resource('cli')")  # type: ignore[arg-type]

    assert captured.get("extra_marker") == "requires_resource('cli')"


@pytest.mark.fast
@pytest.mark.isolation
def test_observability_increment_called_and_exceptions_ignored(monkeypatch: pytest.MonkeyPatch):
    """ReqID: CLI-RT-12 — Observability increments and exceptions are swallowed."""
    stub = StubBridge()
    monkeypatch.setattr(rtc, "bridge", stub, raising=False)

    called = {"count": 0}

    def fake_increment(*args: Any, **kwargs: Any) -> None:
        called["count"] += 1

    monkeypatch.setattr(rtc, "increment_counter", fake_increment)

    def fake_run_tests(*args: Any, **kwargs: Any) -> tuple[bool, str]:
        return True, "ok"

    monkeypatch.setattr(rtc, "run_tests", fake_run_tests)

    rtc.run_tests_cmd(target="all-tests", smoke=False)  # type: ignore[arg-type]
    assert called["count"] == 1

    # Now raise inside increment and ensure no crash
    def raise_increment(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(rtc, "increment_counter", raise_increment)
    rtc.run_tests_cmd(target="all-tests", smoke=False)  # type: ignore[arg-type]


@pytest.mark.fast
@pytest.mark.isolation
def test_success_and_failure_paths(monkeypatch: pytest.MonkeyPatch):
    """ReqID: CLI-RT-13 — Success prints success; failure prints error and exits with code 1."""
    import click

    stub = StubBridge()
    monkeypatch.setattr(rtc, "bridge", stub, raising=False)

    # Success path
    monkeypatch.setattr(rtc, "run_tests", lambda *a, **k: (True, "ok"))
    rtc.run_tests_cmd(target="unit-tests", smoke=False)  # type: ignore[arg-type]
    assert any("Tests completed successfully" in m for m in stub.messages)

    # Failure path
    monkeypatch.setattr(rtc, "run_tests", lambda *a, **k: (False, "bad"))
    with pytest.raises((SystemExit, click.exceptions.Exit)) as excinfo:  # type: ignore[attr-defined]
        rtc.run_tests_cmd(target="unit-tests", smoke=False)  # type: ignore[arg-type]
    val = excinfo.value
    code = getattr(val, "code", getattr(val, "exit_code", None))
    assert code == 1
    assert any("Tests failed" in m for m in stub.messages)


@pytest.mark.fast
@pytest.mark.isolation
def test_unit_tests_default_allows_requests(monkeypatch: pytest.MonkeyPatch):
    """ReqID: CLI-RT-14 — unit-tests default sets DEVSYNTH_TEST_ALLOW_REQUESTS=true when unset."""
    stub = StubBridge()
    monkeypatch.setattr(rtc, "bridge", stub, raising=False)

    monkeypatch.delenv("DEVSYNTH_TEST_ALLOW_REQUESTS", raising=False)

    def fake_run_tests(*args: Any, **kwargs: Any) -> tuple[bool, str]:
        return True, "ok"

    monkeypatch.setattr(rtc, "run_tests", fake_run_tests)

    rtc.run_tests_cmd(target="unit-tests", smoke=False)  # type: ignore[arg-type]
    assert os.environ.get("DEVSYNTH_TEST_ALLOW_REQUESTS") == "true"


@pytest.mark.fast
@pytest.mark.isolation
def test_bridge_override_is_used(monkeypatch: pytest.MonkeyPatch, capsys):
    """ReqID: CLI-RT-15 — Provided bridge instance is used if it's a UXBridge; otherwise default bridge prints to stdout."""
    custom = StubBridge()

    def fake_run_tests(*args: Any, **kwargs: Any) -> tuple[bool, str]:
        return True, "custom-output"

    monkeypatch.setattr(rtc, "run_tests", fake_run_tests)

    rtc.run_tests_cmd(target="unit-tests", smoke=False, bridge=custom)  # type: ignore[arg-type]

    # Since StubBridge is not an instance of UXBridge, fallback bridge is used.
    out = capsys.readouterr().out
    assert "custom-output" in out
