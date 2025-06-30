from devsynth.application.cli.setup_wizard import SetupWizard
from devsynth.interface.ux_bridge import UXBridge


class DummyBridge(UXBridge):
    def __init__(self, answers, confirms) -> None:
        self.answers = list(answers)
        self.confirms = list(confirms)
        self.messages = []

    def ask_question(self, *a, **k):
        return self.answers.pop(0)

    def confirm_choice(self, *a, **k):
        return self.confirms.pop(0)

    def display_result(self, message: str, *, highlight: bool = False) -> None:
        self.messages.append(message)


def test_setup_wizard_instantiation() -> None:
    wizard = SetupWizard()
    assert isinstance(wizard, SetupWizard)


def test_setup_wizard_run(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    answers = [
        str(tmp_path),
        "single_package",
        "python",
        "",
        "kuzu",
    ]
    confirms = [
        True,  # offline mode
        True,  # wsde_collaboration
        False,  # dialectical_reasoning
        False,  # code_generation
        False,  # test_generation
        False,  # documentation_generation
        False,  # experimental_features
        True,  # proceed
    ]
    bridge = DummyBridge(answers, confirms)
    wizard = SetupWizard(bridge)
    cfg = wizard.run()
    cfg_file = tmp_path / ".devsynth" / "project.yaml"
    assert cfg_file.exists()
    assert cfg.config.memory_store_type == "kuzu"
    assert cfg.config.offline_mode is True
    assert cfg.config.features["wsde_collaboration"] is True
    assert "Initialization complete" in bridge.messages[-1]


def test_setup_wizard_abort(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    answers = [
        str(tmp_path),
        "single_package",
        "python",
        "",
        "memory",
    ]
    confirms = [
        False,  # offline mode
        False,  # wsde_collaboration
        False,  # dialectical_reasoning
        False,  # code_generation
        False,  # test_generation
        False,  # documentation_generation
        False,  # experimental_features
        False,  # proceed
    ]
    bridge = DummyBridge(answers, confirms)
    wizard = SetupWizard(bridge)
    wizard.run()
    cfg_file = tmp_path / ".devsynth" / "project.yaml"
    assert not cfg_file.exists()
    assert "Initialization aborted." in bridge.messages[-1]
