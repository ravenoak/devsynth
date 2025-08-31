from pathlib import Path

import pytest
import yaml

from devsynth.core.config_loader import load_config


@pytest.mark.fast
def test_load_config_merges_mvuu_settings(tmp_path):
    mvu_cfg = {"schema": "s.json", "storage": {"path": "db.json", "format": "json"}}
    dev_dir = tmp_path / ".devsynth"
    dev_dir.mkdir()
    (dev_dir / "mvu.yml").write_text(yaml.safe_dump(mvu_cfg))
    cfg = load_config(start_path=str(tmp_path))
    assert cfg.mvuu == mvu_cfg
