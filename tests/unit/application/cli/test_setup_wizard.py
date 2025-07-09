from devsynth.application.cli.setup_wizard import SetupWizard
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge


class DummyBridge(UXBridge):

    def __init__(self, answers, confirms) ->None:
        self.answers = list(answers)
        self.confirms = list(confirms)
        self.messages = []

    def ask_question(self, *a, **k):
        return self.answers.pop(0)

    def confirm_choice(self, *a, **k):
        return self.confirms.pop(0)

    def display_result(self, message: str, *, highlight: bool=False) ->None:
        self.messages.append(message)


def test_setup_wizard_instantiation_succeeds() ->None:
    """Test that setup wizard instantiation succeeds.

ReqID: N/A"""
    wizard = SetupWizard()
    assert isinstance(wizard.bridge, CLIUXBridge)


def test_wizard_prompts_via_cli_bridge_succeeds(tmp_path, monkeypatch) ->None:
    """Ensure the wizard uses CLIUXBridge for prompting.

ReqID: N/A"""
    monkeypatch.chdir(tmp_path)
    answers = iter([str(tmp_path), 'single_package', 'python', '',
        'my goal', 'memory'])
    confirms = iter([False, False, False, False, False, False, False, True])
    asked = []
    confirmed = []
    monkeypatch.setattr(CLIUXBridge, 'ask_question', lambda self, msg, **k:
        asked.append(msg) or next(answers))
    monkeypatch.setattr(CLIUXBridge, 'confirm_choice', lambda self, msg, **
        k: confirmed.append(msg) or next(confirms))
    monkeypatch.setattr(CLIUXBridge, 'display_result', lambda self, m, **k:
        None)
    wizard = SetupWizard()
    cfg = wizard.run()
    assert cfg.path.exists()
    assert asked[0].startswith('Project root')


def test_setup_wizard_run_succeeds(tmp_path, monkeypatch) ->None:
    """Test that setup wizard run succeeds.

ReqID: N/A"""
    monkeypatch.chdir(tmp_path)
    answers = [str(tmp_path), 'single_package', 'python', '', 'do stuff',
        'kuzu']
    confirms = [True, True, False, False, False, False, False, True]
    bridge = DummyBridge(answers, confirms)
    wizard = SetupWizard(bridge)
    cfg = wizard.run()
    cfg_file = tmp_path / '.devsynth' / 'devsynth.yml'
    assert cfg_file.exists()
    assert cfg.config.goals == 'do stuff'
    assert cfg.config.memory_store_type == 'kuzu'
    assert cfg.config.offline_mode is True
    assert cfg.config.features['wsde_collaboration'] is True
    assert 'Initialization complete' in bridge.messages[-1]


def test_setup_wizard_abort_succeeds(tmp_path, monkeypatch) ->None:
    """Test that setup wizard abort succeeds.

ReqID: N/A"""
    monkeypatch.chdir(tmp_path)
    answers = [str(tmp_path), 'single_package', 'python', '', '', 'memory']
    confirms = [False, False, False, False, False, False, False, False]
    bridge = DummyBridge(answers, confirms)
    wizard = SetupWizard(bridge)
    wizard.run()
    cfg_file = tmp_path / '.devsynth' / 'devsynth.yml'
    assert not cfg_file.exists()
    assert 'Initialization aborted.' in bridge.messages[-1]
