from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import pytest

ingest_module = importlib.import_module("devsynth.application.cli.commands.ingest_cmd")


@pytest.mark.fast
def test_ingest_cli_command_uses_typed_options(monkeypatch, tmp_path: Path) -> None:
    """The Typer command forwards typed options to the implementation."""

    captured: dict[str, Any] = {}

    def fake_ingest_cmd(**kwargs: Any) -> None:
        captured.update(kwargs)

    monkeypatch.setattr(ingest_module, "_ingest_cmd", fake_ingest_cmd)

    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text("{}")

    ingest_module.ingest_cmd(
        manifest_path=manifest_path,
        dry_run=True,
        verbose=True,
        validate_only=False,
        yes=True,
        priority="high",
        auto_phase_transitions=False,
        defaults=True,
        non_interactive=True,
        bridge=None,
    )

    assert captured["manifest_path"] == manifest_path
    assert isinstance(captured["manifest_path"], Path)
    assert captured["bridge"] is not None
    assert captured["non_interactive"] is True
    assert captured["defaults"] is True
