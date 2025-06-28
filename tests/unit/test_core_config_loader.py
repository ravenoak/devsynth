import os
from pathlib import Path
from devsynth.core.config_loader import load_config, save_global_config, CoreConfig


def test_precedence_env_over_project_over_global(tmp_path, monkeypatch):
    # set up fake home
    home = tmp_path / "home"
    global_dir = home / ".devsynth" / "config"
    global_dir.mkdir(parents=True)
    (global_dir / "global_config.yaml").write_text("language: python\n")

    # project config
    project_dir = tmp_path / "project"
    project_cfg_dir = project_dir / ".devsynth"
    project_cfg_dir.mkdir(parents=True, exist_ok=True)
    (project_cfg_dir / "devsynth.yml").write_text("language: python\n")

    monkeypatch.setattr(
        os.path,
        "expanduser",
        lambda x: str(home) if x == "~" else os.path.expanduser(x),
    )
    monkeypatch.setenv("DEVSYNTH_LANGUAGE", "rust")

    cfg = load_config(str(project_dir))
    assert cfg.language == "rust"


def test_load_toml_project(tmp_path, monkeypatch):
    project_dir = tmp_path / "project2"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[tool.devsynth]\nlanguage = 'java'\n")

    cfg = load_config(str(project_dir))
    assert cfg.language == "java"


def test_save_global_config_yaml(tmp_path, monkeypatch):
    home = tmp_path / "home"
    monkeypatch.setattr(
        os.path,
        "expanduser",
        lambda x: str(home) if x == "~" else os.path.expanduser(x),
    )

    cfg = CoreConfig(language="python")
    path = save_global_config(cfg)
    assert path.exists()
    loaded = load_config(start_path=tmp_path)
    assert loaded.language == "python"
