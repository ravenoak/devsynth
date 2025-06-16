from pathlib import Path
from devsynth.config.loader import load_config, config_key_autocomplete

def test_load_yaml_config(tmp_path):
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    (cfg_dir / "devsynth.yml").write_text("language: python\n")
    cfg = load_config(tmp_path)
    assert cfg.language == "python"

def test_load_pyproject_toml(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[tool.devsynth]\nlanguage='go'\n")
    cfg = load_config(tmp_path)
    assert cfg.language == "go"

def test_autocomplete(monkeypatch, tmp_path):
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    (cfg_dir / "devsynth.yml").write_text("language: python\n")
    monkeypatch.chdir(tmp_path)
    result = config_key_autocomplete(None, "l")
    assert "language" in result
