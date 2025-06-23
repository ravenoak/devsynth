import pytest
from devsynth.config.loader import load_config, ConfigurationError


def test_load_config_merges_defaults(tmp_path):
    dev_dir = tmp_path / ".devsynth"
    dev_dir.mkdir()
    (dev_dir / "devsynth.yml").write_text("language: python\n")

    cfg = load_config(tmp_path)

    assert cfg.language == "python"
    assert cfg.directories["source"] == ["src"]
    assert cfg.features["code_generation"] is False


def test_malformed_yaml_raises(tmp_path):
    dev_dir = tmp_path / ".devsynth"
    dev_dir.mkdir()
    (dev_dir / "devsynth.yml").write_text(": - bad")

    with pytest.raises(ConfigurationError):
        load_config(tmp_path)


def test_malformed_toml_raises(tmp_path):
    toml_path = tmp_path / "pyproject.toml"
    toml_path.write_text("[tool.devsynth\nfoo = 'bar'")

    with pytest.raises(ConfigurationError):
        load_config(tmp_path)
