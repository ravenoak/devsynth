import os
from typing import Any

import pytest

from devsynth.application.cli.commands.run_tests_cmd import run_tests_cmd


@pytest.fixture(autouse=True)
def _patch_coverage_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "devsynth.application.cli.commands.run_tests_cmd.enforce_coverage_threshold",
        lambda *a, **k: 100.0,
    )


class DummyBridge:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def print(self, msg: str) -> None:  # match UXBridge protocol
        self.messages.append(msg)
        print(msg)


@pytest.mark.fast
def test_feature_flags_set_env_and_success_message(monkeypatch, capsys):
    """ReqID: TR-CLI-01 — Feature flags set env and UX success message."""
    # Arrange: capture env changes and stub run_tests to succeed
    called: dict[str, Any] = {}

    def fake_run_tests(
        target: str,
        speed_categories,
        verbose: bool,
        report: bool,
        parallel: bool,
        segment: bool,
        segment_size: int,
        maxfail,
        **kwargs: Any,
    ) -> tuple[bool, str]:
        called.update(
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
        return True, "OK"

    monkeypatch.setattr(
        "devsynth.application.cli.commands.run_tests_cmd.run_tests", fake_run_tests
    )

    # Ensure a clean slate for feature flags
    for k in list(os.environ.keys()):
        if k.startswith("DEVSYNTH_FEATURE_"):
            os.environ.pop(k)

    bridge = DummyBridge()
    # Use our dummy bridge by overriding the module-level bridge (programmatic path)
    monkeypatch.setattr(
        "devsynth.application.cli.commands.run_tests_cmd.bridge", bridge, raising=False
    )

    # Act: provide three feature flags (true by default, explicit false, numeric zero)
    run_tests_cmd(
        target="unit-tests",
        speeds=["fast"],
        features=["foo", "bar=false", "baz=0"],
    )

    # Assert: env variables are set according to feature map
    assert os.environ["DEVSYNTH_FEATURE_FOO"] == "true"
    assert os.environ["DEVSYNTH_FEATURE_BAR"] == "false"
    assert os.environ["DEVSYNTH_FEATURE_BAZ"] == "false"

    # Success message surfaced
    cout = capsys.readouterr().out
    assert "Tests completed successfully" in cout

    # The stub received a fast speed selection
    assert called["speed_categories"] == ["fast"]


@pytest.mark.fast
def test_marker_option_is_passed_as_extra_marker(monkeypatch):
    """ReqID: TR-CLI-02 — --marker is passed through as extra_marker."""
    recorded: dict[str, Any] = {}

    def fake_run_tests(
        target: str,
        speed_categories,
        verbose: bool,
        report: bool,
        parallel: bool,
        segment: bool,
        segment_size: int,
        maxfail,
        **kwargs: Any,
    ):
        recorded.update(kwargs)
        return True, ""

    monkeypatch.setattr(
        "devsynth.application.cli.commands.run_tests_cmd.run_tests", fake_run_tests
    )

    bridge = DummyBridge()

    run_tests_cmd(
        target="unit-tests",
        speeds=["fast"],
        marker="requires_resource('cli')",
        bridge=bridge,  # type: ignore[arg-type]
    )

    assert recorded.get("extra_marker") == "requires_resource('cli')"
