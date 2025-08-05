import pytest
from pathlib import Path
import textwrap
from devsynth.config.unified_loader import UnifiedConfigLoader


@pytest.mark.medium
def test_gui_and_mvuu_dashboard_flags_recognized(tmp_path: Path) -> None:
    """Test that gui and mvuu_dashboard feature flags are recognized.

    ReqID: N/A"""
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    cfg_file = cfg_dir / "project.yaml"
    cfg_file.write_text(
        textwrap.dedent(
            """
            version: "1.0"
            features:
              gui: true
              mvuu_dashboard: true
            """
        )
    )
    config = UnifiedConfigLoader.load(path=str(tmp_path))
    assert config.config.features["gui"] is True
    assert config.config.features["mvuu_dashboard"] is True
