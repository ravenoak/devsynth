import pytest
from pathlib import Path
import toml
import yaml
from devsynth.application.config.unified_config_loader import UnifiedConfigLoader

@pytest.mark.medium
def test_load_from_yaml_succeeds(tmp_path: Path) -> None:
    cfg_dir = tmp_path / '.devsynth'
    cfg_dir.mkdir()
    (cfg_dir / 'project.yaml').write_text('language: python\n')
    unified = UnifiedConfigLoader.load(tmp_path)
    assert unified.use_pyproject is False
    assert unified.path == cfg_dir / 'project.yaml'
    assert unified.config.language == 'python'

@pytest.mark.medium
def test_load_from_pyproject_succeeds(tmp_path: Path) -> None:
    toml_path = tmp_path / 'pyproject.toml'
    toml_path.write_text("[tool.devsynth]\nlanguage = 'python'\n")
    unified = UnifiedConfigLoader.load(tmp_path)
    assert unified.use_pyproject is True
    assert unified.path == toml_path
    assert unified.config.language == 'python'

@pytest.mark.medium
def test_save_and_exists_succeeds(tmp_path: Path) -> None:
    cfg_dir = tmp_path / '.devsynth'
    unified = UnifiedConfigLoader.load(tmp_path)
    assert not unified.exists()
    unified.set_language('python')
    save_path = unified.save()
    assert save_path == cfg_dir / 'project.yaml'
    assert unified.exists()
    unified = UnifiedConfigLoader.load(tmp_path)
    assert unified.exists()
    save_path = unified.save()
    assert save_path == unified.path

@pytest.mark.medium
def test_loader_save_function_yaml_succeeds(tmp_path: Path) -> None:
    cfg = UnifiedConfigLoader.load(tmp_path)
    cfg.set_language('go')
    path = UnifiedConfigLoader.save(cfg)
    data = yaml.safe_load(path.read_text())
    assert data['language'] == 'go'

@pytest.mark.medium
def test_loader_save_function_pyproject_succeeds(tmp_path: Path) -> None:
    toml_path = tmp_path / 'pyproject.toml'
    toml_path.write_text('[tool.devsynth]\n')
    cfg = UnifiedConfigLoader.load(tmp_path)
    cfg.set_language('rust')
    path = UnifiedConfigLoader.save(cfg)
    data = toml.load(path)
    assert data['tool']['devsynth']['language'] == 'rust'