import pytest

from devsynth.config.loader import ConfigurationError, load_config


@pytest.mark.medium
def test_load_config_merges_defaults_succeeds(tmp_path):
    """Test that load config merges defaults succeeds.

    ReqID: N/A"""
    dev_dir = tmp_path / ".devsynth"
    dev_dir.mkdir()
    (dev_dir / "project.yaml").write_text("language: python\n")
    cfg = load_config(tmp_path)
    assert cfg.language == "python"
    assert cfg.directories["source"] == ["src"]
    assert cfg.features["code_generation"] is False


@pytest.mark.medium
def test_malformed_yaml_raises(tmp_path):
    """Test that malformed yaml raises.

    ReqID: N/A"""
    dev_dir = tmp_path / ".devsynth"
    dev_dir.mkdir()
    (dev_dir / "project.yaml").write_text(": - bad")
    with pytest.raises(ConfigurationError):
        load_config(tmp_path)


@pytest.mark.medium
def test_malformed_toml_raises(tmp_path):
    """Test that malformed toml raises.

    ReqID: N/A"""
    toml_path = tmp_path / "pyproject.toml"
    toml_path.write_text("[tool.devsynth\nfoo = 'bar'")
    with pytest.raises(ConfigurationError):
        load_config(tmp_path)
