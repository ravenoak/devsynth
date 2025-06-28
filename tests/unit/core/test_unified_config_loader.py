from devsynth.config.unified_loader import UnifiedConfigLoader
import toml


def test_unified_loader_detects_yaml(tmp_path):
    """use_pyproject is False when only YAML config exists."""
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    (cfg_dir / "devsynth.yml").write_text("language: python\n")

    unified = UnifiedConfigLoader.load(tmp_path)

    assert not unified.use_pyproject


def test_unified_loader_detects_pyproject(tmp_path):
    """use_pyproject is True when pyproject.toml exists."""
    (tmp_path / "pyproject.toml").write_text("[tool.devsynth]\nlanguage = 'python'\n")

    unified = UnifiedConfigLoader.load(tmp_path)

    assert unified.use_pyproject


def test_unified_loader_prefers_pyproject(tmp_path):
    """pyproject.toml is used when both config files exist."""
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    (cfg_dir / "devsynth.yml").write_text("language: python\n")
    (tmp_path / "pyproject.toml").write_text("[tool.devsynth]\nlanguage = 'python'\n")

    unified = UnifiedConfigLoader.load(tmp_path)

    assert unified.use_pyproject
    assert unified.config.language == "python"


def test_unified_config_save_updates_pyproject(tmp_path):
    """Saving config with use_pyproject=True updates the TOML table."""
    (tmp_path / "pyproject.toml").write_text("[tool.devsynth]\nlanguage='python'\n")

    unified = UnifiedConfigLoader.load(tmp_path)
    unified.set_language("python")
    unified.save()

    data = toml.load(tmp_path / "pyproject.toml")
    assert data["tool"]["devsynth"]["language"] == "python"


def test_unified_config_exists_for_both_formats(tmp_path):
    """exists() returns True for YAML and TOML configurations."""
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    (cfg_dir / "devsynth.yml").write_text("language: python\n")
    assert UnifiedConfigLoader.load(tmp_path).exists()

    (tmp_path / "pyproject.toml").write_text("[tool.devsynth]\nlanguage='python'\n")
    assert UnifiedConfigLoader.load(tmp_path).exists()
