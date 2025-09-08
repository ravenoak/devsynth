# flake8: noqa: E501
import os

import pytest
import typer

from devsynth.application.cli.commands.run_tests_cmd import run_tests_cmd
from devsynth.interface.ux_bridge import UXBridge


class DummyBridge(UXBridge):
    def __init__(self) -> None:
        self.messages: list[str] = []

    def ask_question(self, message: str, *, choices=None, default=None, show_default=True) -> str:  # type: ignore[override]
        return default or ""

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:  # type: ignore[override]
        return default

    def display_result(self, message: str, *, highlight: bool = False, message_type: str | None = None) -> None:  # type: ignore[override]
        self.messages.append(message)


@pytest.mark.fast
def test_marker_anding_passthrough_multiple_speeds(monkeypatch) -> None:
    """ReqID: CLI-RT-11b — CLI forwards multiple speeds and marker for ANDing.

    This ensures that the CLI boundary preserves multiple --speed values and the
    --marker expression so that the underlying runner can build the correct
    pytest '-m' expression (ANDed filters).
    """

    captured: dict[str, object] = {}

    def fake_run_tests(*args, **kwargs):  # noqa: ANN001
        captured["args"] = args
        captured["kwargs"] = kwargs
        return True, "OK"

    monkeypatch.setattr(
        "devsynth.application.cli.commands.run_tests_cmd.run_tests", fake_run_tests
    )

    bridge = DummyBridge()

    run_tests_cmd(
        target="unit-tests",
        speeds=["fast", "medium"],
        marker="property",
        bridge=bridge,
    )

    # Positional args for run_tests are:
    # 0 target, 1 speed_categories, 2 verbose, 3 report, 4 parallel, ...
    assert captured["args"][0] == "unit-tests"
    assert captured["args"][1] == ["fast", "medium"]  # type: ignore[index]
    assert captured["kwargs"].get("extra_marker") == "property"  # type: ignore[union-attr]
    # CLI should emit success message from happy path
    assert any("Tests completed successfully" in m for m in bridge.messages)


@pytest.mark.fast
def test_invalid_marker_expression_exits_cleanly(monkeypatch) -> None:
    """ReqID: CLI-RT-15 — Invalid marker expression leads to clean non-zero exit.

    We simulate an invalid marker by having the underlying runner return
    (False, <error output>), and assert the CLI prints a failure message and
    exits with non-zero status code.
    """

    def fake_run_tests(*args, **kwargs):  # noqa: ANN001
        return False, "ERROR: bad marker expression near 'and (foo or)'"

    monkeypatch.setattr(
        "devsynth.application.cli.commands.run_tests_cmd.run_tests", fake_run_tests
    )

    bridge = DummyBridge()

    with pytest.raises(typer.Exit) as ei:
        run_tests_cmd(
            target="unit-tests",
            speeds=["fast"],
            marker="(foo or)",
            bridge=bridge,
        )

    assert ei.value.exit_code == 1
    # Check that a red failure message was printed
    assert any("Tests failed" in m for m in bridge.messages)
