import json
import os

import pytest
import yaml
from pytest_bdd import given, scenarios, then, when

from devsynth.application.cli.config import CLIConfig
from devsynth.application.cli.requirements_wizard import requirements_wizard

scenarios("../features/general/interactive_requirements.feature")


@pytest.mark.medium
@given("the DevSynth CLI is installed")
def cli_installed():
    return True


@pytest.mark.medium
@when("I run the interactive requirements wizard")
def run_wizard(tmp_project_dir):
    class Bridge:
        def display_result(self, *a, **k):
            pass

    output = os.path.join(tmp_project_dir, "requirements_wizard.json")
    requirements_wizard(
        Bridge(),
        output_file=output,
        title="Sample title",
        description="Sample description",
        req_type="functional",
        priority="medium",
        constraints="",
        config=CLIConfig(non_interactive=True),
    )


@pytest.mark.medium
@then('a structured requirements file "requirements_wizard.json" should exist')
def check_file(tmp_project_dir):
    path = os.path.join(tmp_project_dir, "requirements_wizard.json")
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data.get("title") == "Sample title"

    cfg_path = os.path.join(tmp_project_dir, ".devsynth", "project.yaml")
    cfg = yaml.safe_load(open(cfg_path))
    assert cfg.get("priority") == "medium"
    assert cfg.get("constraints") == ""
