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
