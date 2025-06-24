from devsynth.config.unified_loader import UnifiedConfigLoader


def test_unified_loader_detects_yaml(tmp_path):
    """use_pyproject is False when only YAML config exists."""
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    (cfg_dir / "devsynth.yml").write_text("language: python\n")

    unified = UnifiedConfigLoader.load(tmp_path)

    assert not unified.use_pyproject


def test_unified_loader_detects_pyproject(tmp_path):
    """use_pyproject is True when pyproject.toml exists."""
    (tmp_path / "pyproject.toml").write_text("[tool.devsynth]\nlanguage = 'go'\n")

    unified = UnifiedConfigLoader.load(tmp_path)

    assert unified.use_pyproject
