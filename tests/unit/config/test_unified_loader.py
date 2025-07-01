import toml
import yaml
from pathlib import Path

from devsynth.config.unified_loader import UnifiedConfigLoader
from devsynth.config.loader import ConfigModel


def test_loads_from_pyproject(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(f"[tool.devsynth]\nversion = '{ConfigModel.version}'\n")

    unified = UnifiedConfigLoader.load(tmp_path)

    assert unified.use_pyproject is True
    assert unified.path == pyproject
    assert unified.config.version == ConfigModel.version


def test_loads_from_yaml(tmp_path: Path) -> None:
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    yaml_file = cfg_dir / "devsynth.yml"
    yaml_file.write_text(f"version: '{ConfigModel.version}'\n")

    unified = UnifiedConfigLoader.load(tmp_path)

    assert unified.use_pyproject is False
    assert unified.path == yaml_file
    assert unified.config.version == ConfigModel.version


def test_save_round_trip_yaml(tmp_path: Path) -> None:
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    yaml_file = cfg_dir / "devsynth.yml"
    yaml_file.write_text(f"version: '{ConfigModel.version}'\n")

    unified = UnifiedConfigLoader.load(tmp_path)
    unified.config.language = "python"
    saved = UnifiedConfigLoader.save(unified)

    assert saved == yaml_file
    data = yaml.safe_load(yaml_file.read_text())
    assert data["language"] == "python"


def test_save_round_trip_pyproject(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(f"[tool.devsynth]\nversion = '{ConfigModel.version}'\n")

    unified = UnifiedConfigLoader.load(tmp_path)
    unified.config.language = "python"
    saved = UnifiedConfigLoader.save(unified)

    assert saved == pyproject
    content = toml.load(pyproject)
    assert content["tool"]["devsynth"]["language"] == "python"
