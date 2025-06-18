import os
import yaml
from devsynth.application.cli.cli_commands import init_cmd, gather_cmd


def test_gather_updates_config(tmp_path):
    os.chdir(tmp_path)
    init_cmd(path=str(tmp_path))
    answers = ["goal1", "constraint1", "high"]

    class Bridge:
        def __init__(self):
            self.i = 0

        def ask_question(self, *a, **k):
            val = answers[self.i]
            self.i += 1
            return val

        def confirm_choice(self, *a, **k):
            return True

        def display_result(self, *a, **k):
            pass

    bridge = Bridge()
    gather_cmd(output_file="requirements_plan.yaml", bridge=bridge)

    cfg_path = tmp_path / ".devsynth" / "devsynth.yml"
    data = yaml.safe_load(open(cfg_path))
    assert data.get("priority") == "high"
