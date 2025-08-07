"""Tests for the ``serve_cmd`` CLI command."""

from __future__ import annotations

import builtins
import importlib

import pytest


@pytest.mark.medium
def test_serve_cmd_missing_uvicorn_succeeds(monkeypatch):
    """``serve_cmd`` should warn when ``uvicorn`` is missing."""

    outputs: list[str] = []
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.split(".")[0] == "uvicorn":
            raise ImportError("No module named 'uvicorn'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    module = importlib.import_module("devsynth.application.cli.commands.serve_cmd")

    class DummyBridge:
        def display_result(
            self, msg: str, *, highlight: bool = False
        ) -> None:  # noqa: FBT001, FBT002
            outputs.append(msg)

    module.serve_cmd(bridge=DummyBridge())

    assert any("uvicorn" in msg.lower() for msg in outputs)
