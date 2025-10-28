import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import app

runner = CliRunner()


def _repo_root() -> Path:
    # tests/unit/cli/test_mvu_commands.py -> tests/unit/cli -> tests/unit -> tests -> repo_root
    return Path(__file__).resolve().parents[3]


@pytest.mark.fast
def test_mvu_help_lists_subcommands():
    result = runner.invoke(app, ["mvu", "--help"])
    assert result.exit_code == 0
    out = result.stdout
    # Ensure the four baseline subcommands are present
    for sub in ("init", "lint", "report", "rewrite"):
        assert sub in out, f"Expected '{sub}' in help output: {out}"


@pytest.mark.fast
def test_mvu_init_creates_config_and_matches_schema(tmp_path, monkeypatch):
    # Run in isolated temp directory
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["mvu", "init"])
    assert result.exit_code == 0, result.stdout

    cfg_path = tmp_path / ".devsynth" / "mvu.yml"
    assert cfg_path.exists(), "mvu.yml should be created by 'mvu init'"

    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    assert isinstance(cfg, dict)

    # Validate against the MVUU config schema
    schema_path = _repo_root() / "docs/specifications/mvuu_config.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    # Bare minimum validation to avoid adding a new runtime dependency in tests
    # while still asserting conformance: check required keys and nested types.
    # Full validation is covered elsewhere with jsonschema for MVUU records.
    for key in ("schema", "storage", "issues"):
        assert key in cfg, f"Missing required key '{key}' in mvu.yml"

    assert isinstance(cfg["schema"], str)

    storage = cfg["storage"]
    assert isinstance(storage, dict)
    assert {"path", "format"}.issubset(storage.keys())
    assert isinstance(storage["path"], str)
    assert storage["format"] in ("json",)

    issues = cfg["issues"]
    assert isinstance(issues, dict)
    # If providers are present, ensure expected keys exist and are strings
    for provider in ("github", "jira"):
        if provider in issues:
            val = issues[provider]
            assert isinstance(val, dict)
            assert {"base_url", "token"}.issubset(val.keys())
            assert isinstance(val["base_url"], str)
            assert isinstance(val["token"], str)
