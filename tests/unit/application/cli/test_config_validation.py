"""Tests for configuration validation via ``doctor_cmd``."""

from pathlib import Path
from textwrap import dedent
from unittest.mock import patch

import importlib
import pytest


doctor_cmd = importlib.import_module(
    "devsynth.application.cli.commands.doctor_cmd"
)


@pytest.mark.medium
def test_config_warnings_succeeds(tmp_path, monkeypatch):
    """Doctor command reports configuration issues when validation fails."""

    monkeypatch.setattr(doctor_cmd.sys, "version_info", (3, 11, 0))
    monkeypatch.setenv("OPENAI_API_KEY", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "1")

    config_dir = tmp_path / "cfg"
    config_dir.mkdir()
    (config_dir / "default.yml").write_text(
        "application: {name: App, version: '1.0'}\n"
    )

    real_spec = doctor_cmd.importlib.util.spec_from_file_location

    def fake_spec(name, location, *args, **kwargs):
        path = Path(__file__).parents[4] / "scripts" / "validate_config.py"
        return real_spec(name, path, *args, **kwargs)

    with patch.object(
        doctor_cmd.importlib.util,
        "spec_from_file_location",
        side_effect=fake_spec,
    ), patch.object(doctor_cmd, "load_config"), patch.object(
        doctor_cmd.bridge, "print"
    ) as mock_print:
        doctor_cmd.doctor_cmd(str(config_dir))
        output = "".join(str(c.args[0]) for c in mock_print.call_args_list)
        assert "Configuration issues detected" in output


VALID_CONFIG = dedent(
    """
    application:
      name: App
      version: "1.0"
    logging:
      level: INFO
      format: "%(message)s"
    memory:
      default_store: kuzu
      stores:
        chromadb:
          enabled: true
        kuzu: {}
        faiss:
          enabled: false
    llm:
      default_provider: openai
      providers:
        openai:
          enabled: true
    agents:
      max_agents: 1
      default_timeout: 1
    edrr:
      enabled: false
      default_phase: expand
    security:
      input_validation: true
    performance: {}
    features:
      wsde_collaboration: false
    """
)


@pytest.mark.medium
def test_config_success_succeeds(tmp_path, monkeypatch):
    """Doctor command reports success when all configs are valid."""

    monkeypatch.setattr(doctor_cmd.sys, "version_info", (3, 11, 0))
    monkeypatch.setenv("OPENAI_API_KEY", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "1")
    monkeypatch.chdir(tmp_path)

    config_dir = tmp_path / "cfg"
    config_dir.mkdir()
    for env in ["default", "development", "testing", "staging", "production"]:
        (config_dir / f"{env}.yml").write_text(VALID_CONFIG)

    # Create expected project directories to avoid warnings
    for name in ("src", "tests", "docs"):
        (tmp_path / name).mkdir()

    real_spec = doctor_cmd.importlib.util.spec_from_file_location

    def fake_spec(name, location, *args, **kwargs):
        path = Path(__file__).parents[4] / "scripts" / "validate_config.py"
        return real_spec(name, path, *args, **kwargs)

    with patch.object(
        doctor_cmd.importlib.util,
        "spec_from_file_location",
        side_effect=fake_spec,
    ), patch.object(doctor_cmd, "load_config"), patch.object(
        doctor_cmd, "_find_project_config", return_value=tmp_path
    ), patch.object(doctor_cmd.bridge, "print") as mock_print:
        doctor_cmd.doctor_cmd(str(config_dir))
        output = "".join(str(c.args[0]) for c in mock_print.call_args_list)
        assert "All configuration files are valid" in output

