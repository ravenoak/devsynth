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
        "DEVSYNTH_PROVIDER",
        "DEVSYNTH_OFFLINE",
        "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE",
    ]
    for k in keys:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(rtc, "enforce_coverage_threshold", lambda *a, **k: 100.0)
    yield
    for k in keys:
        monkeypatch.delenv(k, raising=False)


@pytest.mark.fast
def test_provider_defaults_are_applied_when_unset(monkeypatch: pytest.MonkeyPatch):
    """ReqID: CLI-RT-18 — Provider defaults applied when unset.

    run_tests_cmd should set conservative defaults for provider/env when they are
    not already specified by the environment:
      - DEVSYNTH_PROVIDER=stub
      - DEVSYNTH_OFFLINE=true
      - DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=false
    """
    stub = StubBridge()
    monkeypatch.setattr(rtc, "bridge", stub, raising=False)

    def fake_run_tests(*args: Any, **kwargs: Any) -> tuple[bool, str]:
        return True, "ok"

    monkeypatch.setattr(rtc, "run_tests", fake_run_tests)

    # Call with a minimal invocation path
    rtc.run_tests_cmd(target="unit-tests", speeds=["fast"], smoke=False)  # type: ignore[arg-type]

    assert os.environ.get("DEVSYNTH_PROVIDER") == "stub"
    assert os.environ.get("DEVSYNTH_OFFLINE") == "true"
    assert os.environ.get("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE") == "false"


@pytest.mark.fast
def test_provider_defaults_do_not_override_existing(monkeypatch: pytest.MonkeyPatch):
    """ReqID: CLI-RT-18b — Existing provider env values are respected.

    If the caller has already set provider/offline flags, the CLI should not
    override them when configuring defaults.
    """
    stub = StubBridge()
    monkeypatch.setattr(rtc, "bridge", stub, raising=False)

    def fake_run_tests(*args: Any, **kwargs: Any) -> tuple[bool, str]:
        return True, "ok"

    monkeypatch.setattr(rtc, "run_tests", fake_run_tests)

    # Pre-set env values that differ from defaults
    monkeypatch.setenv("DEVSYNTH_PROVIDER", "openai")
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "false")
    monkeypatch.setenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "true")

    rtc.run_tests_cmd(target="unit-tests", speeds=["fast"], smoke=False)  # type: ignore[arg-type]

    # Values should remain as pre-set
    assert os.environ.get("DEVSYNTH_PROVIDER") == "openai"
    assert os.environ.get("DEVSYNTH_OFFLINE") == "false"
    assert os.environ.get("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE") == "true"
