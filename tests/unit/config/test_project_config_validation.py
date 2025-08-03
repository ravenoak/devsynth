import pytest
from devsynth.config import ProjectUnifiedConfig
from devsynth.exceptions import DevSynthError
from pathlib import Path
VALID_CONFIG = """
projectName: demo
version: 0.1.0
structure:
  type: single_package
  directories:
    source: ["src"]
"""
INVALID_CONFIG = """
version: 0.1.0
structure:
  type: single_package
  directories:
    source: ["src"]
"""


@pytest.mark.medium
def test_valid_project_config_loads_succeeds(tmp_path: Path):
    """Test that valid project config loads succeeds.

ReqID: N/A"""
    cfg_dir = tmp_path / '.devsynth'
    cfg_dir.mkdir()
    (cfg_dir / 'project.yaml').write_text(VALID_CONFIG)
    cfg = ProjectUnifiedConfig.load(tmp_path)
    assert cfg.config.project_root == str(tmp_path)


@pytest.mark.medium
def test_invalid_project_config_raises(tmp_path: Path):
    """Test that invalid project config raises.

ReqID: N/A"""
    cfg_dir = tmp_path / '.devsynth'
    cfg_dir.mkdir()
    (cfg_dir / 'project.yaml').write_text(INVALID_CONFIG)
    with pytest.raises(DevSynthError):
        ProjectUnifiedConfig.load(tmp_path)
