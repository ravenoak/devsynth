from pathlib import Path

import yaml
import toml

from devsynth.application.cli.cli_commands import init_cmd
from devsynth.interface.cli import CLIUXBridge


def _run_init(tmp_path, monkeypatch, *, use_pyproject=False):
    """Helper to run init_cmd with patched bridge."""
    monkeypatch.chdir(tmp_path)

    answers = iter([str(tmp_path), "python", "do stuff"])
    monkeypatch.setattr(
        "devsynth.interface.cli.Prompt.ask", lambda *a, **k: next(answers)
    )
    monkeypatch.setattr("devsynth.interface.cli.Confirm.ask", lambda *a, **k: True)
    printed = []
    monkeypatch.setattr(
        "rich.console.Console.print",
        lambda self, msg, *, highlight=False: printed.append(msg),
    )
    if use_pyproject:
        (tmp_path / "pyproject.toml").write_text("")
    bridge = CLIUXBridge()
    init_cmd(bridge=bridge)
    return printed


def _load_config(path: Path):
    if path.suffix == ".toml":
        return toml.load(path)["tool"]["devsynth"]
    return yaml.safe_load(path.read_text())


def test_init_cmd_creates_config(tmp_path, monkeypatch):
    printed = _run_init(tmp_path, monkeypatch)
    cfg_file = tmp_path / ".devsynth" / "project.yaml"
    if not cfg_file.exists():
        cfg_file = tmp_path / ".devsynth" / "devsynth.yml"
    if not cfg_file.exists():
        cfg_file = tmp_path / "pyproject.toml"
    data = _load_config(cfg_file)
    assert data["project_root"] == str(tmp_path)
    assert data["language"] == "python"
    assert data["goals"] == "do stuff"
    assert any("Initialization complete" in msg for msg in printed)


def test_init_cmd_idempotent(tmp_path, monkeypatch):
    _run_init(tmp_path, monkeypatch)
    printed = _run_init(tmp_path, monkeypatch)
    assert any("Project already initialized" in msg for msg in printed)
