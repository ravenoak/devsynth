import pytest

from devsynth.application.cli.cli_commands import init_cmd
from devsynth.config.unified_loader import UnifiedConfigLoader
from devsynth.interface.cli import CLIUXBridge


def _run_init(tmp_path, features, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "devsynth.application.cli.cli_commands.init_project", lambda **kwargs: None
    )
    bridge = CLIUXBridge()
    init_cmd(
        root=str(tmp_path),
        language="python",
        goals="do stuff",
        memory_backend="memory",
        offline_mode=False,
        features=features,
        auto_confirm=True,
        bridge=bridge,
    )
    return UnifiedConfigLoader.load(tmp_path).config


@pytest.mark.fast
def test_init_cmd_accepts_feature_list(tmp_path, monkeypatch):
    cfg = _run_init(tmp_path, ["code_generation", "test_generation"], monkeypatch)
    assert cfg.features["code_generation"] is True
    assert cfg.features["test_generation"] is True


@pytest.mark.fast
def test_init_cmd_accepts_feature_json(tmp_path, monkeypatch):
    cfg = _run_init(
        tmp_path,
        ['{"code_generation": true, "test_generation": false}'],
        monkeypatch,
    )
    assert cfg.features["code_generation"] is True
    assert cfg.features["test_generation"] is False
