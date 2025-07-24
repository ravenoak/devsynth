import os
import yaml
from unittest.mock import patch
from devsynth.application.cli.cli_commands import init_cmd, gather_cmd


def test_gather_updates_config_succeeds(tmp_path):
    """Test that gather updates config succeeds.

    ReqID: N/A"""
    os.chdir(tmp_path)
    init_cmd(
        root=str(tmp_path),
        language="python",
        goals="",
        memory_backend="memory",
        auto_confirm=True,
    )
    answers = ["goal1", "constraint1", "high"]

    class Bridge:

        def __init__(self):
            self.i = 0

        def ask_question(self, *a, **k):
            val = answers[self.i]
            self.i += 1
            return val

        def prompt(self, *a, **k):
            return self.ask_question(*a, **k)

        def confirm_choice(self, *a, **k):
            return True

        def confirm(self, *a, **k):
            return True

        def display_result(self, *a, **k):
            pass

    bridge = Bridge()
    gather_cmd(output_file="requirements_plan.yaml", bridge=bridge)
    cfg_path = tmp_path / ".devsynth" / "project.yaml"
    data = yaml.safe_load(open(cfg_path))
    assert data.get("priority") == "high"
