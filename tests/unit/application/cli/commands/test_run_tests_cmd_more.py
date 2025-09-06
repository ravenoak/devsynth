import os
from typing import Any

import pytest

import devsynth.application.cli.commands.run_tests_cmd as rtc


class StubBridge:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def print(self, msg: str) -> None:
        self.messages.append(str(msg))


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch):
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
def test_speed_and_marker_forwarding(monkeypatch: pytest.MonkeyPatch):
    """ReqID: CLI-RT-07 — --speed and -m forwarded to runner correctly."""
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
        return True, "fine"

    monkeypatch.setattr(rtc, "run_tests", fake_run_tests)

    rtc.run_tests_cmd(
        target="unit-tests",
        speeds=["fast", "SLOW"],
        smoke=False,
        no_parallel=True,
        report=False,
        verbose=False,
        segment=False,
        segment_size=50,
        maxfail=3,
        marker="requires_resource('lmstudio')",
    )

    assert captured["speed_categories"] == ["fast", "slow"]
    # extra marker is forwarded via kwargs as extra_marker
    assert captured["kwargs"].get("extra_marker") == "requires_resource('lmstudio')"
    # maxfail forwarded
    assert captured["maxfail"] == 3


@pytest.mark.fast
@pytest.mark.isolation
def test_report_true_prints_output_and_success(monkeypatch: pytest.MonkeyPatch):
    """ReqID: CLI-RT-08 — --report True forwards and prints success message."""
    stub = StubBridge()
    monkeypatch.setattr(rtc, "bridge", stub, raising=False)

    def fake_run_tests(*args: Any, **kwargs: Any) -> tuple[bool, str]:
        assert args[3] is True  # report flag position per signature
        return True, "OUTPUT"

    monkeypatch.setattr(rtc, "run_tests", fake_run_tests)

    rtc.run_tests_cmd(target="unit-tests", report=True, speeds=["fast"])  # type: ignore[arg-type]

    # Output printed and success message
    assert any("OUTPUT" in m for m in stub.messages)
    assert any("Tests completed successfully" in m for m in stub.messages)


@pytest.mark.fast
@pytest.mark.isolation
def test_observability_and_error_path(monkeypatch: pytest.MonkeyPatch):
    """ReqID: CLI-RT-09 — increment_counter is called; failure prints and exits 1."""
    stub = StubBridge()
    monkeypatch.setattr(rtc, "bridge", stub, raising=False)

    calls: list[tuple[str, dict[str, str]]] = []

    def fake_increment_counter(name: str, labels: dict[str, str], description: str | None = None) -> None:  # noqa: ARG001
        calls.append((name, labels))

    monkeypatch.setattr(rtc, "increment_counter", fake_increment_counter)

    def fake_run_tests(*args: Any, **kwargs: Any) -> tuple[bool, str]:
        return False, "FAIL_OUTPUT"

    monkeypatch.setattr(rtc, "run_tests", fake_run_tests)

    import click

    with pytest.raises((SystemExit, click.exceptions.Exit)) as excinfo:  # type: ignore[attr-defined]
        rtc.run_tests_cmd(target="unit-tests", report=False, speeds=["fast"])  # type: ignore[arg-type]

    val = excinfo.value
    code = getattr(val, "code", getattr(val, "exit_code", None))
    assert code == 1

    # Failure message printed
    assert any("Tests failed" in m for m in stub.messages)
    # Observability call recorded
    assert calls and calls[0][0] == "devsynth_cli_run_tests_invocations"
    assert calls[0][1].get("target") == "unit-tests"
