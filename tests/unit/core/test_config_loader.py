import os
from devsynth.config.loader import ConfigModel, load_config
from devsynth.config import load_project_config


def test_load_from_dev_synth_yaml_succeeds(tmp_path, monkeypatch):
    """Load configuration from .devsynth/project.yaml.

ReqID: N/A"""
    home = tmp_path / 'home'
    monkeypatch.setattr(os.path, 'expanduser', lambda p: str(home) if p ==
        '~' else os.path.expanduser(p))
    cfg_dir = tmp_path / '.devsynth'
    cfg_dir.mkdir()
    (cfg_dir / 'project.yaml').write_text('language: python\n')
    cfg = load_config(tmp_path)
    assert cfg.language == 'python'


def test_load_from_pyproject_toml_succeeds(tmp_path, monkeypatch):
    """Load configuration from pyproject.toml.

ReqID: N/A"""
    home = tmp_path / 'home'
    monkeypatch.setattr(os.path, 'expanduser', lambda p: str(home) if p ==
        '~' else os.path.expanduser(p))
    (tmp_path / 'pyproject.toml').write_text(
        "[tool.devsynth]\nlanguage = 'python'\n")
    cfg = load_config(tmp_path)
    assert cfg.language == 'python'


def test_yaml_toml_equivalence_succeeds(tmp_path, monkeypatch):
    """YAML and TOML configs load to the same ConfigModel data.

ReqID: N/A"""
    home = tmp_path / 'home'
    monkeypatch.setattr(os.path, 'expanduser', lambda p: str(home) if p ==
        '~' else os.path.expanduser(p))
    cfg_dir = tmp_path / '.devsynth'
    cfg_dir.mkdir()
    (cfg_dir / 'project.yaml').write_text(
        """language: python
directories:
  source: ['src']
  tests: ['tests']
"""
        )
    cfg_yaml = load_config(tmp_path)
    (cfg_dir / 'project.yaml').unlink()
    (tmp_path / 'pyproject.toml').write_text(
        """[tool.devsynth]
language = 'python'
directories = {source=['src'], tests=['tests']}
"""
        )
    cfg_toml = load_config(tmp_path)
    assert cfg_yaml.as_dict() == cfg_toml.as_dict()


def test_load_project_config_yaml_succeeds(tmp_path):
    """load_project_config reads .devsynth/project.yaml.

ReqID: N/A"""
    cfg_dir = tmp_path / '.devsynth'
    cfg_dir.mkdir()
    (cfg_dir / 'project.yaml').write_text('language: python\n')
    cfg = load_project_config(tmp_path)
    assert cfg.config.language == 'python'
    assert cfg.path == cfg_dir / 'project.yaml'


def test_load_project_config_pyproject_succeeds(tmp_path):
    """load_project_config reads [tool.devsynth] table.

ReqID: N/A"""
    (tmp_path / 'pyproject.toml').write_text(
        "[tool.devsynth]\nlanguage = 'python'\n")
    cfg = load_project_config(tmp_path)
    assert cfg.config.language == 'python'
    assert cfg.use_pyproject
