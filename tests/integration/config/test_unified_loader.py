import os
from pathlib import Path

import pytest

from devsynth.config.loader import ConfigModel
from devsynth.config.unified_loader import UnifiedConfigLoader


def _setup_project(project_dir: Path) -> None:
    """Create both YAML and TOML configs in the given directory."""
    dev_dir = project_dir / ".devsynth"
    dev_dir.mkdir(parents=True, exist_ok=True)
    (dev_dir / "project.yaml").write_text(f"version: '{ConfigModel.version}'\n")
    (project_dir / "pyproject.toml").write_text(
        f"""[tool.devsynth]
version = '{ConfigModel.version}'
"""
    )


@pytest.mark.medium
def test_unified_loader_prefers_pyproject_succeeds(tmp_path):
    """Test that unified loader prefers pyproject succeeds.

    ReqID: N/A"""
    _setup_project(tmp_path)
    unified = UnifiedConfigLoader.load(tmp_path)
    assert unified.use_pyproject
    assert unified.path.name == "pyproject.toml"
    assert unified.config.version == ConfigModel.version


@pytest.mark.medium
def test_env_var_override_with_custom_path_succeeds(monkeypatch, tmp_path):
    """Test that env var override with custom path succeeds.

    ReqID: N/A"""
    env_project = tmp_path / "env_project"
    env_project.mkdir()
    _setup_project(env_project)
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(env_project))
    other_project = tmp_path / "other_project"
    other_project.mkdir()
    _setup_project(other_project)
    os.chdir(tmp_path)
    unified = UnifiedConfigLoader.load(other_project)
    assert unified.use_pyproject
    assert unified.config.project_root == str(other_project)
    assert unified.config.version == ConfigModel.version
