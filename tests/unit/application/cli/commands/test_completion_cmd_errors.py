"""CLI completion error handling guardrails (see completion_cmd.py:232-369)."""

from collections.abc import Callable
from typing import Any

import pytest
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import build_app
from devsynth.application.cli.commands import completion_cmd as module


class StubBridge:
    """Minimal UX bridge capturing messages emitted by ``completion_cmd``."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, str | None]] = []

    def display_result(
        self,
        message: str,
        *,
        highlight: bool | None = None,
        message_type: str | None = None,
    ) -> None:
        self.messages.append((message, message_type))


def _no_progress(_: str, task_fn: Callable[[], Any], __: Any, *, total: int = 1) -> Any:
    """Test helper to bypass progress rendering while executing ``task_fn``."""

    return task_fn()


@pytest.mark.medium
def test_cli_completion_rejects_invalid_shell(monkeypatch) -> None:
    """Invalid shells surface actionable messages (run_tests via Typer)."""

    bridge = StubBridge()
    monkeypatch.setattr(module, "bridge", bridge)
    app = build_app()

    runner = CliRunner()
    result = runner.invoke(app, ["completion", "--shell", "bogus"])

    assert result.exit_code == 0
    assert any("Unsupported shell: bogus" in msg for msg, _ in bridge.messages)


@pytest.mark.medium
def test_cli_completion_detects_shell_when_unspecified(monkeypatch, tmp_path) -> None:
    """Shell auto-detection and script echo follow completion_cmd.py flow."""

    bridge = StubBridge()
    monkeypatch.setattr(module, "bridge", bridge)
    monkeypatch.setattr(module, "detect_shell", lambda: "fish")
    monkeypatch.setattr(module, "run_with_progress", _no_progress)

    script_path = tmp_path / "devsynth-completion.fish"
    script_path.write_text("function __devsynth_complete")
    monkeypatch.setattr(
        module,
        "generate_completion_script",
        lambda shell, output=None: str(script_path),
    )

    app = build_app()
    runner = CliRunner()
    result = runner.invoke(app, ["completion"])

    assert result.exit_code == 0
    assert ("Detected shell: fish", "info") in bridge.messages
    assert any("Shell completion script for fish" in msg for msg, _ in bridge.messages)


@pytest.mark.medium
def test_cli_completion_reports_generation_errors(monkeypatch) -> None:
    """Filesystem failures during generation bubble up with error context."""

    bridge = StubBridge()
    monkeypatch.setattr(module, "bridge", bridge)
    monkeypatch.setattr(module, "detect_shell", lambda: "bash")
    monkeypatch.setattr(module, "run_with_progress", _no_progress)

    def _raise_generate(*_: Any, **__: Any) -> str:
        raise FileNotFoundError("script not bundled")

    monkeypatch.setattr(module, "generate_completion_script", _raise_generate)

    app = build_app()
    runner = CliRunner()
    result = runner.invoke(app, ["completion"])

    assert result.exit_code == 0
    assert any(
        "Failed to generate completion script" in msg
        for msg, kind in bridge.messages
        if kind == "error"
    )


@pytest.mark.medium
def test_cli_completion_reports_install_errors(monkeypatch) -> None:
    """Installation path issues emit informative error messaging."""

    bridge = StubBridge()
    monkeypatch.setattr(module, "bridge", bridge)
    monkeypatch.setattr(module, "run_with_progress", _no_progress)

    def _raise_install(*_: Any, **__: Any) -> str:
        raise FileNotFoundError("target directory unavailable")

    monkeypatch.setattr(module, "install_completion_script", _raise_install)

    app = build_app()
    runner = CliRunner()
    result = runner.invoke(app, ["completion", "--shell", "bash", "--install"])

    assert result.exit_code == 0
    assert any(
        "Failed to install completion script" in msg
        for msg, kind in bridge.messages
        if kind == "error"
    )
