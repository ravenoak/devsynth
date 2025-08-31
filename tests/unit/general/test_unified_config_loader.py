import logging
from pathlib import Path

import pytest
import toml
import yaml

from devsynth.config.unified_loader import UnifiedConfigLoader


@pytest.mark.fast
def test_load_from_yaml_succeeds(tmp_path: Path) -> None:
    """Test that load from yaml succeeds.

    ReqID: N/A"""
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    (cfg_dir / "project.yaml").write_text("language: python\n")
    unified = UnifiedConfigLoader.load(tmp_path)
    assert not unified.use_pyproject
    assert unified.path == cfg_dir / "project.yaml"
    assert unified.config.language == "python"


@pytest.mark.fast
def test_load_from_pyproject_succeeds(tmp_path: Path) -> None:
    """Test that load from pyproject succeeds.

    ReqID: N/A"""
    toml_path = tmp_path / "pyproject.toml"
    toml_path.write_text("[tool.devsynth]\nlanguage = 'python'\n")
    unified = UnifiedConfigLoader.load(tmp_path)
    assert unified.use_pyproject
    assert unified.path == toml_path
    assert unified.config.language == "python"


@pytest.mark.fast
def test_save_and_exists_succeeds(tmp_path: Path) -> None:
    """Test that save and exists succeeds.

    ReqID: N/A"""
    cfg_dir = tmp_path / ".devsynth"
    unified = UnifiedConfigLoader.load(tmp_path)
    assert not unified.exists()
    unified.set_language("python")
    save_path = unified.save()
    assert save_path == cfg_dir / "project.yaml"
    assert unified.exists()
    unified = UnifiedConfigLoader.load(tmp_path)
    assert unified.exists()
    save_path = unified.save()
    assert save_path == unified.path


@pytest.mark.fast
def test_missing_files_succeeds(tmp_path: Path) -> None:
    """Test that missing files succeeds.

    ReqID: N/A"""
    unified = UnifiedConfigLoader.load(tmp_path)
    assert not unified.exists()
    assert unified.path == tmp_path / ".devsynth" / "project.yaml"


@pytest.mark.fast
def test_version_mismatch_warning_succeeds(tmp_path: Path, caplog) -> None:
    """Test that version mismatch warning succeeds.

    ReqID: N/A"""
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    (cfg_dir / "project.yaml").write_text("version: '0.0'\n")
    caplog.set_level(logging.WARNING)
    UnifiedConfigLoader.load(tmp_path)
    assert any("version" in rec.message for rec in caplog.records)


@pytest.mark.fast
def test_loader_save_function_yaml_succeeds(tmp_path: Path) -> None:
    """Test that loader save function yaml succeeds.

    ReqID: N/A"""
    cfg = UnifiedConfigLoader.load(tmp_path)
    cfg.set_language("go")
    path = UnifiedConfigLoader.save(cfg)
    data = yaml.safe_load(path.read_text())
    assert data["language"] == "go"


@pytest.mark.fast
def test_loader_save_function_pyproject_succeeds(tmp_path: Path) -> None:
    """Test that loader save function pyproject succeeds.

    ReqID: N/A"""
    toml_path = tmp_path / "pyproject.toml"
    toml_path.write_text("[tool.devsynth]\n")
    cfg = UnifiedConfigLoader.load(tmp_path)
    cfg.set_language("rust")
    path = UnifiedConfigLoader.save(cfg)
    data = toml.load(path)
    assert data["tool"]["devsynth"]["language"] == "rust"
