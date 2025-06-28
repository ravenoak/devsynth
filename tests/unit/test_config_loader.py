from pathlib import Path
import logging
import yaml
from devsynth.config.loader import (
    load_config,
    config_key_autocomplete,
    save_config,
    ConfigModel,
)

def test_load_yaml_config(tmp_path):
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    (cfg_dir / "devsynth.yml").write_text("language: python\n")
    cfg = load_config(tmp_path)
    assert cfg.language == "python"

def test_load_pyproject_toml(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[tool.devsynth]\nlanguage='python'\n")
    cfg = load_config(tmp_path)
    assert cfg.language == "python"

def test_autocomplete(monkeypatch, tmp_path):
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    (cfg_dir / "devsynth.yml").write_text("language: python\n")
    monkeypatch.chdir(tmp_path)
    result = config_key_autocomplete(None, "l")
    assert "language" in result


def test_save_persists_version(tmp_path):
    cfg = ConfigModel(project_root=str(tmp_path))
    path = save_config(cfg, path=str(tmp_path))
    data = yaml.safe_load(path.read_text())
    assert data["version"] == cfg.version


def test_version_mismatch_logs_warning(tmp_path, caplog):
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    (cfg_dir / "devsynth.yml").write_text("version: '0.0'\n")
    caplog.set_level(logging.WARNING)
    load_config(tmp_path)
    assert any("version" in rec.message for rec in caplog.records)
