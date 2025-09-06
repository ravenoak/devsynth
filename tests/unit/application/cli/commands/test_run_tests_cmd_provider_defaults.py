"""Provider defaults behavior tests for run-tests CLI.

Covers Task 2.5: Ensure offline/stub defaults are enforced by run-tests for unit paths.

Acceptance Criteria:
- When DEVSYNTH_PROVIDER and DEVSYNTH_OFFLINE are unset, run-tests sets them to
  stub/true via ProviderEnv.with_test_defaults().apply_to_env().
- Tests pass without external provider calls.

Markers: @pytest.mark.fast (speed discipline)
"""
from __future__ import annotations

import os
from typing import Any

import pytest

# Target under test
import devsynth.application.cli.commands.run_tests_cmd as rtc


class StubBridge:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def print(self, msg: str) -> None:  # pragma: no cover - trivial
        self.messages.append(str(msg))


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch):
    # Ensure a clean slate for env vars we mutate
    keys = [
        "DEVSYNTH_PROVIDER",
        "DEVSYNTH_OFFLINE",
        "OPENAI_API_KEY",
        "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
        "PYTEST_ADDOPTS",
    ]
    for k in keys:
        monkeypatch.delenv(k, raising=False)
    yield
    for k in keys:
        monkeypatch.delenv(k, raising=False)


@pytest.mark.fast
@pytest.mark.isolation
def test_defaults_applied_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """When provider/offline are unset, CLI should set stub/true defaults."""
    # Arrange
    stub = StubBridge()
    monkeypatch.setattr(rtc, "bridge", stub, raising=False)

    # Stub out run_tests to avoid invoking pytest
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
        captured.update(dict(target=target, speed_categories=speed_categories))
        return True, "ok"

    monkeypatch.setattr(rtc, "run_tests", fake_run_tests)

    # Act
    rtc.run_tests_cmd(target="unit-tests", smoke=False, speeds=["fast"])  # type: ignore[arg-type]

    # Assert provider defaults
    assert os.environ.get("DEVSYNTH_PROVIDER") == "stub"
    assert os.environ.get("DEVSYNTH_OFFLINE") == "true"
    # LM Studio availability should default to false unless explicitly set
    assert os.environ.get("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE") == "false"
    # Deterministic placeholder should be present for OpenAI key
    assert os.environ.get("OPENAI_API_KEY") == "test-openai-key"


@pytest.mark.fast
@pytest.mark.isolation
def test_respects_pre_set_env_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """If user pre-sets provider/offline, CLI should not override them."""
    # Arrange
    stub = StubBridge()
    monkeypatch.setattr(rtc, "bridge", stub, raising=False)

    # Pre-set values simulating a user override
    os.environ["DEVSYNTH_PROVIDER"] = "openai"
    os.environ["DEVSYNTH_OFFLINE"] = "false"
    os.environ["DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"] = "true"

    def fake_run_tests(*args: Any, **kwargs: Any) -> tuple[bool, str]:
        return True, "ok"

    monkeypatch.setattr(rtc, "run_tests", fake_run_tests)

    # Act
    rtc.run_tests_cmd(target="unit-tests", smoke=False, speeds=["fast"])  # type: ignore[arg-type]

    # Assert values remain as set
    assert os.environ.get("DEVSYNTH_PROVIDER") == "openai"
    assert os.environ.get("DEVSYNTH_OFFLINE") == "false"
    # Availability should remain true because it was explicitly set
    assert os.environ.get("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE") == "true"