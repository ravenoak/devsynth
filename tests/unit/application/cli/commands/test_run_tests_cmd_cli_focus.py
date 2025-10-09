"""Focused CLI regression tests for ``run_tests_cmd`` Typer wiring."""

from __future__ import annotations

import json
import os
from pathlib import Path
from types import ModuleType

import pytest
from typer import Typer

from devsynth.interface.ux_bridge import UXBridge
from tests.helpers.typer import invoke
from tests.unit.application.cli.commands.helpers import build_minimal_cli_app


class RecordingBridge(UXBridge):
    """Capture UX output for assertions without touching real IO."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def ask_question(
        self,
        message: str,
        *,
        choices: list[str] | None = None,
        default: str | None = None,
        show_default: bool = True,
    ) -> str:  # type: ignore[override]
        return default or ""

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:  # type: ignore[override]
        return default

    def display_result(
        self,
        message: str,
        *,
        highlight: bool = False,
        message_type: str | None = None,
    ) -> None:  # type: ignore[override]
        self.messages.append(message)


@pytest.fixture
def cli_app(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[ModuleType, Typer, RecordingBridge]:
    """Load the CLI command with a stub bridge and patched coverage helpers."""

    app, module = build_minimal_cli_app(monkeypatch)

    bridge = RecordingBridge()
    monkeypatch.setattr(module, "bridge", bridge)
    monkeypatch.setattr(
        module, "pytest_cov_support_status", lambda env=None: (True, None)
    )
    monkeypatch.setattr(module, "coverage_artifacts_status", lambda: (True, None))
    monkeypatch.setattr(
        module, "enforce_coverage_threshold", lambda exit_on_failure=False: 97.0
    )
    monkeypatch.setattr(module, "ensure_pytest_cov_plugin_env", lambda env: False)
    monkeypatch.setattr(module, "ensure_pytest_bdd_plugin_env", lambda env: False)

    return module, app, bridge


@pytest.mark.fast
def test_cli_marker_passthrough(
    cli_app: tuple[ModuleType, Typer, RecordingBridge],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CLI should forward ``--marker`` to the runner as ``extra_marker``."""

    module, app, bridge = cli_app
    captured: dict[str, object] = {}

    def fake_run_tests(*args: object, **kwargs: object) -> tuple[bool, str]:
        captured["args"] = args
        captured["kwargs"] = kwargs
        return True, "ok"

    monkeypatch.setattr(module, "run_tests", fake_run_tests)

    result = invoke(
        app,
        [
            "--target",
            "unit-tests",
            "--speed",
            "fast",
            "--marker",
            "requires_resource('chroma')",
        ],
    )

    assert result.exit_code == 0
    assert captured["kwargs"].get("extra_marker") == "requires_resource('chroma')"
    assert any("Tests completed successfully" in msg for msg in bridge.messages)


@pytest.mark.fast
def test_cli_feature_flags_set_environment(
    cli_app: tuple[ModuleType, Typer, RecordingBridge],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``--feature`` flags should map to ``DEVSYNTH_FEATURE_<NAME>`` env vars."""

    module, app, _bridge = cli_app
    monkeypatch.setattr(module, "run_tests", lambda *a, **k: (True, ""))
    monkeypatch.delenv("DEVSYNTH_FEATURE_ALPHA", raising=False)
    monkeypatch.delenv("DEVSYNTH_FEATURE_BETA", raising=False)

    result = invoke(
        app,
        [
            "--target",
            "unit-tests",
            "--speed",
            "fast",
            "--feature",
            "alpha",
            "--feature",
            "beta=false",
        ],
    )

    assert result.exit_code == 0
    assert os.environ["DEVSYNTH_FEATURE_ALPHA"] == "true"
    assert os.environ["DEVSYNTH_FEATURE_BETA"] == "false"


@pytest.mark.fast
def test_cli_segmentation_arguments_forwarded(
    cli_app: tuple[ModuleType, Typer, RecordingBridge],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Segmentation options should propagate to ``run_tests`` positional args."""

    module, app, _bridge = cli_app
    captured: dict[str, object] = {}

    def fake_run_tests(*args: object, **kwargs: object) -> tuple[bool, str]:
        captured["args"] = args
        captured["kwargs"] = kwargs
        return True, "segmented"

    monkeypatch.setattr(module, "run_tests", fake_run_tests)

    result = invoke(
        app,
        [
            "--target",
            "unit-tests",
            "--speed",
            "fast",
            "--segment",
            "--segment-size",
            "25",
        ],
    )

    assert result.exit_code == 0
    forwarded_args = captured["args"]
    assert forwarded_args[5] is True  # segment flag
    assert forwarded_args[6] == 25  # segment size


@pytest.mark.fast
def test_cli_inventory_mode_exports_json(
    cli_app: tuple[ModuleType, Typer, RecordingBridge],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Inventory mode should write ``test_inventory.json`` and bypass pytest."""

    module, app, _bridge = cli_app
    calls: list[tuple[str, str | None]] = []

    def fake_collect(target: str, speed: str | None, **_: object) -> list[str]:
        calls.append((target, speed))
        return [f"{target}::{speed or 'all'}::test_example"]

    monkeypatch.setattr(module, "collect_tests_with_cache", fake_collect)
    monkeypatch.setattr(
        module,
        "run_tests",
        lambda *a, **k: (_ for _ in ()).throw(
            AssertionError("run_tests should not execute")
        ),
    )

    monkeypatch.chdir(tmp_path)

    result = invoke(app, ["--inventory"])

    assert result.exit_code == 0
    inventory_path = tmp_path / "test_reports" / "test_inventory.json"
    assert inventory_path.exists()
    payload = json.loads(inventory_path.read_text())
    assert set(payload["targets"]) == {
        "all-tests",
        "unit-tests",
        "integration-tests",
        "behavior-tests",
    }
    assert calls  # ensure collection invoked


@pytest.mark.fast
def test_cli_failure_propagates_exit_code(
    cli_app: tuple[ModuleType, Typer, RecordingBridge],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failing pytest invocation should raise ``typer.Exit`` with code 1."""

    module, app, bridge = cli_app
    monkeypatch.setattr(module, "run_tests", lambda *a, **k: (False, "pytest failed"))

    result = invoke(
        app,
        ["--target", "unit-tests", "--speed", "fast"],
    )

    assert result.exit_code == 1
    assert any("Tests failed" in message for message in bridge.messages)
