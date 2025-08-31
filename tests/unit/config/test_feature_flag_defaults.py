"""
Tests to ensure experimental features are disabled by default and toggles work.

ReqID: Task-26
"""

import textwrap
from pathlib import Path

import pytest

from devsynth.config.unified_loader import UnifiedConfigLoader


@pytest.mark.fast
def test_feature_flags_default_off(tmp_path: Path) -> None:
    """Loading with no project config should keep all feature flags False by default."""
    cfg = UnifiedConfigLoader.load(path=str(tmp_path)).config
    # No flag should be enabled by default
    assert isinstance(cfg.features, dict)
    assert all(v is False for v in cfg.features.values())


@pytest.mark.fast
def test_can_enable_known_feature_flag(tmp_path: Path) -> None:
    """Ensure enabling a known feature flag via project.yaml reflects in the config."""
    cfg_dir = tmp_path / ".devsynth"
    cfg_dir.mkdir()
    (cfg_dir / "project.yaml").write_text(
        textwrap.dedent(
            """
            version: "1.0"
            features:
              wsde_collaboration: true
            """
        )
    )
    cfg = UnifiedConfigLoader.load(path=str(tmp_path)).config
    assert cfg.features.get("wsde_collaboration") is True
