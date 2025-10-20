from __future__ import annotations

import importlib
import types
from pathlib import Path

import pytest

doctor_module = importlib.import_module("devsynth.application.cli.commands.doctor_cmd")


class StubBridge:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def print(
        self, message: str, *, highlight: bool = False, message_type: str | None = None
    ) -> None:
        self.messages.append(message)


@pytest.mark.fast
def test_doctor_cmd_accepts_path_arguments(monkeypatch, tmp_path: Path) -> None:
    """``doctor_cmd`` normalizes ``config_dir`` to :class:`Path`."""

    bridge = StubBridge()
    monkeypatch.chdir(tmp_path)
    for required in ("src", "tests", "docs"):
        (tmp_path / required).mkdir(exist_ok=True)
    monkeypatch.setenv("OPENAI_API_KEY", "token")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "token")

    monkeypatch.setattr(
        doctor_module,
        "_get_cli_utils",
        lambda: (lambda *_: None),
    )
    monkeypatch.setattr(
        doctor_module,
        "_get_config_loader",
        lambda: (
            lambda _path: Path("."),
            lambda: types.SimpleNamespace(features={}, memory_store_type="memory"),
        ),
    )
    monkeypatch.setattr(doctor_module.shutil, "which", lambda _: "poetry")
    monkeypatch.setattr(doctor_module.importlib.util, "find_spec", lambda _: object())
    monkeypatch.setattr(doctor_module.sys, "version_info", (3, 12))
    monkeypatch.setattr(doctor_module.sys, "version", "3.12.0")

    class _Loader:
        def exec_module(self, module: types.SimpleNamespace) -> None:
            module.load_config = lambda path: {}
            module.validate_config = lambda data, schema: []
            module.validate_environment_variables = lambda data: []
            module.check_config_consistency = lambda configs: []
            module.CONFIG_SCHEMA = {}

    monkeypatch.setattr(
        doctor_module.importlib.util,
        "spec_from_file_location",
        lambda *_, **__: types.SimpleNamespace(loader=_Loader()),
    )
    monkeypatch.setattr(
        doctor_module.importlib.util,
        "module_from_spec",
        lambda spec: types.SimpleNamespace(),
    )

    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)
    for env in ("default", "development", "testing", "staging", "production"):
        (config_dir / f"{env}.yml").write_text("{}")

    doctor_module.doctor_cmd(config_dir=config_dir, quick=False, bridge=bridge)

    assert any("All configuration files are valid." in msg for msg in bridge.messages)
