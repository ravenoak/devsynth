import pytest

import os
from devsynth.config.loader import load_config


def test_load_config_from_yaml_succeeds(tmp_path):
    """Test that load config from yaml succeeds.

ReqID: N/A"""
    project_dir = tmp_path
    dev_dir = project_dir / '.devsynth'
    dev_dir.mkdir()
    (dev_dir / 'project.yaml').write_text('language: python\n')
    os.chdir(project_dir)
    cfg = load_config(project_dir)
    assert cfg.language == 'python'


@pytest.mark.medium
def test_load_config_from_pyproject_succeeds(tmp_path):
    """Test that load config from pyproject succeeds.

ReqID: N/A"""
    project_dir = tmp_path
    (project_dir / 'pyproject.toml').write_text(
        "[tool.devsynth]\nlanguage = 'python'\n")
    os.chdir(project_dir)
    cfg = load_config(project_dir)
    assert cfg.language == 'python'


@pytest.mark.medium
def test_pyproject_precedence_over_yaml_succeeds(tmp_path):
    """Test that pyproject precedence over yaml succeeds.

ReqID: N/A"""
    project_dir = tmp_path
    dev_dir = project_dir / '.devsynth'
    dev_dir.mkdir()
    (dev_dir / 'project.yaml').write_text('language: python\n')
    (project_dir / 'pyproject.toml').write_text(
        "[tool.devsynth]\nlanguage='python'\n")
    os.chdir(project_dir)
    cfg = load_config(project_dir)
    assert cfg.language == 'python'
