from pathlib import Path

import pytest
import toml
import yaml

from devsynth.config.loader import ConfigModel
from devsynth.config.unified_loader import UnifiedConfigLoader


@pytest.mark.fast
def test_loads_from_pyproject_succeeds(tmp_path: Path) -> None:
    """Test that loads from pyproject succeeds.

    ReqID: N/A"""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(f"[tool.devsynth]\nversion = '{ConfigModel.version}'\n")
    unified = UnifiedConfigLoader.load(tmp_path)
    assert unified.use_pyproject is True
    assert unified.path == pyproject
    assert unified.config.version == ConfigModel.version


@pytest.mark.medium
def test_loads_from_yaml_succeeds(tmp_path: Path) -> None:
    """Test that loads from yaml succeeds.

    ReqID: N/A"""
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    yaml_file = cfg_dir / "project.yaml"
    yaml_file.write_text(f"version: '{ConfigModel.version}'\n")
    unified = UnifiedConfigLoader.load(tmp_path)
    assert unified.use_pyproject is False
    assert unified.path == yaml_file
    assert unified.config.version == ConfigModel.version


@pytest.mark.medium
def test_save_round_trip_yaml_succeeds(tmp_path: Path) -> None:
    """Test that save round trip yaml succeeds.

    ReqID: N/A"""
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    yaml_file = cfg_dir / "project.yaml"
    yaml_file.write_text(f"version: '{ConfigModel.version}'\n")
    unified = UnifiedConfigLoader.load(tmp_path)
    unified.config.language = "python"
    saved = UnifiedConfigLoader.save(unified)
    assert saved == yaml_file
    data = yaml.safe_load(yaml_file.read_text())
    assert data["language"] == "python"


@pytest.mark.medium
def test_save_round_trip_pyproject_succeeds(tmp_path: Path) -> None:
    """Test that save round trip pyproject succeeds.

    ReqID: N/A"""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(f"[tool.devsynth]\nversion = '{ConfigModel.version}'\n")
    unified = UnifiedConfigLoader.load(tmp_path)
    unified.config.language = "python"
    saved = UnifiedConfigLoader.save(unified)
    assert saved == pyproject
    content = toml.load(pyproject)
    assert content["tool"]["devsynth"]["language"] == "python"
