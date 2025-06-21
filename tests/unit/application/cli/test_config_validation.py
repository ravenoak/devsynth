from unittest.mock import patch
from textwrap import dedent

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "doctor_cmd",
    Path(__file__).parents[4]
    / "src"
    / "devsynth"
    / "application"
    / "cli"
    / "commands"
    / "doctor_cmd.py",
)
doctor_cmd = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(doctor_cmd)  # type: ignore


def test_config_warnings(tmp_path, monkeypatch):
    monkeypatch.setattr(doctor_cmd.sys, "version_info", (3, 11, 0))
    monkeypatch.setenv("OPENAI_API_KEY", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "1")

    config_dir = tmp_path / "cfg"
    config_dir.mkdir()

    # intentionally incomplete config to trigger validation errors
    (config_dir / "default.yml").write_text("application: {name: App, version: '1.0'}\n")

    real_spec = doctor_cmd.importlib.util.spec_from_file_location

    def fake_spec(name, location, *args, **kwargs):
        path = Path(__file__).parents[4] / "scripts" / "validate_config.py"
        return real_spec(name, path, *args, **kwargs)

    with patch.object(doctor_cmd.importlib.util, "spec_from_file_location", side_effect=fake_spec), patch.object(doctor_cmd, "load_config"), patch.object(doctor_cmd.bridge, "print") as mock_print:
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


def test_config_success(tmp_path, monkeypatch):
    monkeypatch.setattr(doctor_cmd.sys, "version_info", (3, 11, 0))
    monkeypatch.setenv("OPENAI_API_KEY", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "1")

    config_dir = tmp_path / "cfg"
    config_dir.mkdir()

    for env in ["default", "development", "testing", "staging", "production"]:
        (config_dir / f"{env}.yml").write_text(VALID_CONFIG)

    real_spec = doctor_cmd.importlib.util.spec_from_file_location

    def fake_spec(name, location, *args, **kwargs):
        path = Path(__file__).parents[4] / "scripts" / "validate_config.py"
        return real_spec(name, path, *args, **kwargs)

    with patch.object(doctor_cmd.importlib.util, "spec_from_file_location", side_effect=fake_spec), patch.object(doctor_cmd, "load_config"), patch.object(doctor_cmd.bridge, "print") as mock_print:
        doctor_cmd.doctor_cmd(str(config_dir))
        output = "".join(str(c.args[0]) for c in mock_print.call_args_list)
        assert "All configuration files are valid" in output
