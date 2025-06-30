"""Step definitions for DevSynth doctor command."""

import os
from pytest_bdd import given, then


@given("no DevSynth configuration file in the project")
def no_devsynth_config(tmp_project_dir):
    cfg_yaml = os.path.join(tmp_project_dir, "devsynth.yml")
    if os.path.exists(cfg_yaml):
        os.remove(cfg_yaml)
    legacy = os.path.join(tmp_project_dir, "manifest.yaml")
    if os.path.exists(legacy):
        os.remove(legacy)
    return tmp_project_dir


@then("the output should include onboarding hints")
def output_should_include_hint(command_context):
    output = command_context.get("output", "")
    assert "devsynth init" in output


@then("the output should mention that no project configuration was found")
def output_mentions_missing_project_config(command_context):
    """Ensure the doctor command explains missing configuration."""
    output = command_context.get("output", "")
    assert "No project configuration found" in output


@given("a devsynth.yml file with invalid YAML syntax")
def devsynth_yaml_invalid(tmp_project_dir, monkeypatch):
    """Create a DevSynth config file containing malformed YAML."""
    dev_dir = os.path.join(tmp_project_dir, ".devsynth")
    os.makedirs(dev_dir, exist_ok=True)
    with open(os.path.join(dev_dir, "devsynth.yml"), "w") as f:
        f.write("invalid: [unclosed")
    monkeypatch.chdir(tmp_project_dir)
    return tmp_project_dir


@given("a devsynth.yml file with unsupported configuration keys")
def devsynth_yaml_unsupported_keys(tmp_project_dir, monkeypatch):
    """Create a DevSynth config file containing unknown keys."""
    dev_dir = os.path.join(tmp_project_dir, ".devsynth")
    os.makedirs(dev_dir, exist_ok=True)
    with open(os.path.join(dev_dir, "devsynth.yml"), "w") as f:
        f.write("unsupported_option: true\n")
    monkeypatch.chdir(tmp_project_dir)
    return tmp_project_dir


@given("no .env file exists in the project")
def remove_env_file(tmp_project_dir, monkeypatch):
    """Ensure the project has no .env file."""
    env_path = os.path.join(tmp_project_dir, ".env")
    if os.path.exists(env_path):
        os.remove(env_path)
    monkeypatch.chdir(tmp_project_dir)
    return tmp_project_dir


@then("the output should mention the missing .env file")
def output_mentions_missing_env_file(command_context):
    """Verify that the doctor output references the missing .env file."""
    output = command_context.get("output", "")
    assert ".env" in output
