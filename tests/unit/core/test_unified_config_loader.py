import pytest

from devsynth.config.unified_loader import UnifiedConfigLoader
import toml


def test_unified_loader_detects_yaml_succeeds(tmp_path):
    """use_pyproject is False when only YAML config exists.

ReqID: N/A"""
    cfg_dir = tmp_path / '.devsynth'
    cfg_dir.mkdir()
    (cfg_dir / 'project.yaml').write_text('language: python\n')
    unified = UnifiedConfigLoader.load(tmp_path)
    assert not unified.use_pyproject


@pytest.mark.medium
def test_unified_loader_detects_pyproject_succeeds(tmp_path):
    """use_pyproject is True when pyproject.toml exists.

ReqID: N/A"""
    (tmp_path / 'pyproject.toml').write_text(
        "[tool.devsynth]\nlanguage = 'python'\n")
    unified = UnifiedConfigLoader.load(tmp_path)
    assert unified.use_pyproject


@pytest.mark.medium
def test_unified_loader_prefers_pyproject_succeeds(tmp_path):
    """pyproject.toml is used when both config files exist.

ReqID: N/A"""
    cfg_dir = tmp_path / '.devsynth'
    cfg_dir.mkdir()
    (cfg_dir / 'project.yaml').write_text('language: python\n')
    (tmp_path / 'pyproject.toml').write_text(
        "[tool.devsynth]\nlanguage = 'python'\n")
    unified = UnifiedConfigLoader.load(tmp_path)
    assert unified.use_pyproject
    assert unified.config.language == 'python'


@pytest.mark.medium
def test_unified_config_save_updates_pyproject_succeeds(tmp_path):
    """Saving config with use_pyproject=True updates the TOML table.

ReqID: N/A"""
    (tmp_path / 'pyproject.toml').write_text(
        "[tool.devsynth]\nlanguage='python'\n")
    unified = UnifiedConfigLoader.load(tmp_path)
    unified.set_language('python')
    unified.save()
    data = toml.load(tmp_path / 'pyproject.toml')
    assert data['tool']['devsynth']['language'] == 'python'


@pytest.mark.medium
def test_unified_config_exists_for_both_formats_returns_expected_result(
    tmp_path):
    """exists() returns True for YAML and TOML configurations.

ReqID: N/A"""
    cfg_dir = tmp_path / '.devsynth'
    cfg_dir.mkdir()
    (cfg_dir / 'project.yaml').write_text('language: python\n')
    assert UnifiedConfigLoader.load(tmp_path).exists()
    (tmp_path / 'pyproject.toml').write_text(
        "[tool.devsynth]\nlanguage='python'\n")
    assert UnifiedConfigLoader.load(tmp_path).exists()
