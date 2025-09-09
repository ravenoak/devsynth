import os
from typing import Any, Tuple

import pytest

# Target under test
import devsynth.application.cli.commands.run_tests_cmd as rtc


class StubBridge:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def print(self, msg: str) -> None:
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
    ]
    for k in keys:
        monkeypatch.delenv(k, raising=False)
    yield
    for k in keys:
        monkeypatch.delenv(k, raising=False)


@pytest.mark.fast
@pytest.mark.isolation
def test_inner_test_env_tightening_forces_no_parallel(monkeypatch: pytest.MonkeyPatch):
    # Arrange
    stub = StubBridge()
    monkeypatch.setattr(rtc, "bridge", stub, raising=False)

    # Pretend we're in an inner subprocess run
    os.environ["DEVSYNTH_INNER_TEST"] = "1"

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
        speeds=["fast"],  # explicit to avoid smoke defaulting path
        smoke=False,
        no_parallel=False,
        report=False,
        verbose=False,
        segment=False,
        segment_size=50,
        maxfail=None,
    )

    # Assert environment effects of inner test mode
    assert os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"
    addopts = os.environ.get("PYTEST_ADDOPTS", "")
    assert "-p no:xdist" in addopts and "-p no:cov" in addopts

    # And parallel should be False due to forced no_parallel=True in inner mode
    assert captured["parallel"] is False


@pytest.mark.fast
@pytest.mark.isolation
def test_unit_tests_sets_allow_requests_by_default_and_respects_existing(
    monkeypatch: pytest.MonkeyPatch,
):
    stub = StubBridge()
    monkeypatch.setattr(rtc, "bridge", stub, raising=False)

    def fake_run_tests(*args: Any, **kwargs: Any) -> tuple[bool, str]:
        return True, "ok"

    monkeypatch.setattr(rtc, "run_tests", fake_run_tests)

    # Case 1: Not set initially -> should be set to true for unit-tests when not smoke
    monkeypatch.delenv("DEVSYNTH_TEST_ALLOW_REQUESTS", raising=False)
    rtc.run_tests_cmd(target="unit-tests", smoke=False, report=False, speeds=["fast"])  # type: ignore[arg-type]
    assert os.environ.get("DEVSYNTH_TEST_ALLOW_REQUESTS") == "true"

    # Case 2: Pre-set to false -> should remain unchanged (do not override)
    os.environ["DEVSYNTH_TEST_ALLOW_REQUESTS"] = "false"
    rtc.run_tests_cmd(target="unit-tests", smoke=False, report=False, speeds=["fast"])  # type: ignore[arg-type]
    assert os.environ.get("DEVSYNTH_TEST_ALLOW_REQUESTS") == "false"
