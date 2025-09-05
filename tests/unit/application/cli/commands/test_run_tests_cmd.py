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
