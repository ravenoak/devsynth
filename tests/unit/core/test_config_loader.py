import os

from devsynth.core.config_loader import load_config


def test_load_from_dev_synth_yaml(tmp_path, monkeypatch):
    """Load configuration from .devsynth/devsynth.yml."""
    home = tmp_path / "home"
    monkeypatch.setattr(
        os.path,
        "expanduser",
        lambda p: str(home) if p == "~" else os.path.expanduser(p),
    )

    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    (cfg_dir / "devsynth.yml").write_text("language: python\n")

    cfg = load_config(str(tmp_path))

    assert cfg.language == "python"


def test_load_from_pyproject_toml(tmp_path, monkeypatch):
    """Load configuration from pyproject.toml."""
    home = tmp_path / "home"
    monkeypatch.setattr(
        os.path,
        "expanduser",
        lambda p: str(home) if p == "~" else os.path.expanduser(p),
    )

    (tmp_path / "pyproject.toml").write_text("[tool.devsynth]\nlanguage = 'go'\n")

    cfg = load_config(str(tmp_path))

    assert cfg.language == "go"


def test_env_var_overrides(tmp_path, monkeypatch):
    """Environment variables override file settings."""
    home = tmp_path / "home"
    monkeypatch.setattr(
        os.path,
        "expanduser",
        lambda p: str(home) if p == "~" else os.path.expanduser(p),
    )
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    (cfg_dir / "devsynth.yml").write_text("language: python\n")

    monkeypatch.setenv("DEVSYNTH_LANGUAGE", "rust")

    cfg = load_config(str(tmp_path))

    assert cfg.language == "rust"
