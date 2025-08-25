import runpy
from pathlib import Path

import yaml


def test_mvu_init_cmd_creates_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    repo_root = Path(__file__).resolve().parents[3]
    module = runpy.run_path(
        repo_root / "src/devsynth/application/cli/commands/mvu_init_cmd.py"
    )
    module["mvu_init_cmd"]()
    cfg = yaml.safe_load((tmp_path / ".devsynth" / "mvu.yml").read_text())
    assert cfg["schema"] == "docs/specifications/mvuuschema.json"
    assert cfg["storage"]["path"] == "docs/specifications/mvuu_database.json"
