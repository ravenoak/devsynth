import os
import yaml
from devsynth.application.cli.cli_commands import init_cmd, gather_cmd


def test_gather_updates_config_succeeds(tmp_path):
    """Test that gather updates config succeeds.

ReqID: N/A"""
    os.chdir(tmp_path)
    with patch('devsynth.application.cli.cli_commands.bridge.ask_question',
        side_effect=[str(tmp_path), 'python', '']), patch(
        'devsynth.application.cli.cli_commands.bridge.confirm_choice',
        return_value=True):
        init_cmd()
    answers = ['goal1', 'constraint1', 'high']


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
    gather_cmd(output_file='requirements_plan.yaml', bridge=bridge)
    cfg_path = tmp_path / '.devsynth' / 'project.yaml'
    data = yaml.safe_load(open(cfg_path))
    assert data.get('priority') == 'high'
