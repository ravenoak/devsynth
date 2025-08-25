import logging
from pathlib import Path

import yaml

from devsynth.config.loader import (
    ConfigModel,
    config_key_autocomplete,
    load_config,
    save_config,
)


def test_load_yaml_config_succeeds(tmp_path):
    """Test that load yaml config.

    ReqID: N/A"""
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    (cfg_dir / "project.yaml").write_text("language: python\n")
    cfg = load_config(tmp_path)
    assert cfg.language == "python"


def test_load_pyproject_toml_succeeds(tmp_path):
    """Test that load pyproject toml.

    ReqID: N/A"""
    (tmp_path / "pyproject.toml").write_text("[tool.devsynth]\nlanguage='python'\n")
    cfg = load_config(tmp_path)
    assert cfg.language == "python"


def test_autocomplete_succeeds(monkeypatch, tmp_path):
    """Test that autocomplete succeeds.

    ReqID: N/A"""
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    (cfg_dir / "project.yaml").write_text("language: python\n")
    monkeypatch.chdir(tmp_path)
    result = config_key_autocomplete(None, "l")
    assert "language" in result


def test_save_persists_version_succeeds(tmp_path):
    """Test that save persists version.

    ReqID: N/A"""
    cfg = ConfigModel(project_root=str(tmp_path))
    path = save_config(cfg, path=str(tmp_path))
    data = yaml.safe_load(path.read_text())
    assert data["version"] == cfg.version


def test_version_mismatch_logs_warning_matches_expected(tmp_path, caplog):
    """Test that version mismatch logs warning.

    ReqID: N/A"""
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    (cfg_dir / "project.yaml").write_text("version: '0.0'\n")
    caplog.set_level(logging.WARNING)
    load_config(tmp_path)
    assert any("version" in rec.message for rec in caplog.records)
