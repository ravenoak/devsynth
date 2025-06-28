import os
from devsynth.config.loader import load_config


def test_load_config_from_yaml(tmp_path):
    project_dir = tmp_path
    dev_dir = project_dir / ".devsynth"
    dev_dir.mkdir()
    (dev_dir / "devsynth.yml").write_text("language: python\n")

    os.chdir(project_dir)
    cfg = load_config(project_dir)
    assert cfg.language == "python"


def test_load_config_from_pyproject(tmp_path):
    project_dir = tmp_path
    (project_dir / "pyproject.toml").write_text("[tool.devsynth]\nlanguage = 'python'\n")

    os.chdir(project_dir)
    cfg = load_config(project_dir)
    assert cfg.language == "python"


def test_pyproject_precedence_over_yaml(tmp_path):
    project_dir = tmp_path
    dev_dir = project_dir / ".devsynth"
    dev_dir.mkdir()
    (dev_dir / "devsynth.yml").write_text("language: python\n")
    (project_dir / "pyproject.toml").write_text("[tool.devsynth]\nlanguage='python'\n")

    os.chdir(project_dir)
    cfg = load_config(project_dir)
    assert cfg.language == "python"
