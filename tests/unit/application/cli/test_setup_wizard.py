from pathlib import Path
from unittest.mock import MagicMock

import pytest

from devsynth.application.cli.setup_wizard import SetupWizard
from devsynth.config import ProjectUnifiedConfig
from devsynth.config.loader import ConfigModel
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge

pytestmark = [pytest.mark.fast]


@pytest.fixture(autouse=True)
def disable_prompt_toolkit(monkeypatch):
    """Disable prompt-toolkit integration for legacy wizard tests."""

    monkeypatch.setattr(
        "devsynth.application.cli.setup_wizard.get_prompt_toolkit_adapter", lambda: None
    )


class DummyBridge(UXBridge):
    """Legacy DummyBridge implementation - not recommended for new tests."""

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


class RobustDummyBridge(UXBridge):
    """More robust implementation of DummyBridge with better error handling."""

    def __init__(self, answers, confirms):
        self.answers = list(answers)
        self.confirms = list(confirms)
        self.messages = []
        self.answer_index = 0
        self.confirm_index = 0

    def ask_question(self, *args, **kwargs):
        if self.answer_index < len(self.answers):
            answer = self.answers[self.answer_index]
            self.answer_index += 1
            return answer
        return ""

    def confirm_choice(self, *args, **kwargs):
        if self.confirm_index < len(self.confirms):
            confirm = self.confirms[self.confirm_index]
            self.confirm_index += 1
            return confirm
        return False

    def display_result(self, message, **kwargs):
        self.messages.append(message)


def test_setup_wizard_instantiation_succeeds() -> None:
    """Test that setup wizard instantiation succeeds.

    ReqID: N/A"""
    wizard = SetupWizard()
    assert isinstance(wizard.bridge, CLIUXBridge)


def test_wizard_prompts_via_cli_bridge_succeeds(tmp_path, monkeypatch) -> None:
    """Ensure the wizard uses CLIUXBridge for prompting.

    ReqID: N/A"""
    monkeypatch.chdir(tmp_path)
    answers = [str(tmp_path), "python", "single_package", "", "my goal", "memory"]
    confirms = [False, False, False, False, False, False, False, False, True]
    asked = []
    confirmed = []
    answer_index = 0
    confirm_index = 0

    def mock_ask_question(self, msg, **k):
        nonlocal answer_index
        asked.append(msg)
        if answer_index < len(answers):
            result = answers[answer_index]
            answer_index += 1
            return result
        return ""

    def mock_confirm_choice(self, msg, **k):
        nonlocal confirm_index
        confirmed.append(msg)
        if confirm_index < len(confirms):
            result = confirms[confirm_index]
            confirm_index += 1
            return result
        return False

    monkeypatch.setattr(CLIUXBridge, "ask_question", mock_ask_question)
    monkeypatch.setattr(CLIUXBridge, "confirm_choice", mock_confirm_choice)
    monkeypatch.setattr(CLIUXBridge, "display_result", lambda self, m, **k: None)
    wizard = SetupWizard()
    cfg = wizard.run()
    assert cfg.path.exists()
    assert asked[0].startswith("Project root")


def test_setup_wizard_run_succeeds(tmp_path, monkeypatch) -> None:
    """Test that setup wizard run succeeds.

    ReqID: N/A"""
    monkeypatch.chdir(tmp_path)
    devsynth_dir = tmp_path / ".devsynth"
    devsynth_dir.mkdir(exist_ok=True)
    answers = [str(tmp_path), "python", "single_package", "", "do stuff", "kuzu"]
    confirms = [False, True, True, False, False, False, False, False, True]
    bridge = RobustDummyBridge(answers, confirms)
    wizard = SetupWizard(bridge)
    cfg = wizard.run()
    assert cfg.path.exists()
    assert cfg.config.goals == "do stuff"
    assert cfg.config.memory_store_type == "kuzu"
    assert cfg.config.offline_mode is True
    assert cfg.config.features["wsde_collaboration"] is True
    assert any(("Initialization complete" in msg for msg in bridge.messages))


def test_setup_wizard_abort_succeeds(tmp_path, monkeypatch) -> None:
    """Test that setup wizard abort succeeds.

    ReqID: N/A"""
    monkeypatch.chdir(tmp_path)
    answers = [str(tmp_path), "python", "single_package", "", "", "memory"]
    confirms = [False, False, False, False, False, False, False, False, False]
    bridge = RobustDummyBridge(answers, confirms)
    wizard = SetupWizard(bridge)
    wizard.run()
    cfg_file = tmp_path / ".devsynth" / "project.yaml"
    assert not cfg_file.exists()
    assert any(("Initialization aborted" in msg for msg in bridge.messages))


def test_prompt_features_uses_prompt_toolkit_multiselect(monkeypatch) -> None:
    """When available the wizard should use the prompt-toolkit multi-select dialog."""

    cfg = ProjectUnifiedConfig(ConfigModel(), Path("project.yaml"), False)
    wizard = SetupWizard()
    wizard.progress_manager.update_progress = lambda *_a, **_k: None
    wizard.bridge.display_result = lambda *_a, **_k: None

    adapter = MagicMock()
    adapter.prompt_multi_select.return_value = ["code_generation", "test_generation"]
    monkeypatch.setattr(
        "devsynth.application.cli.setup_wizard.get_prompt_toolkit_adapter",
        lambda: adapter,
    )
    monkeypatch.setattr(
        "devsynth.application.cli.setup_wizard._non_interactive", lambda: False
    )

    features = wizard._prompt_features(cfg, features=None, auto_confirm=False)

    assert features["code_generation"] is True
    assert features["test_generation"] is True
    assert features["wsde_collaboration"] is False
    adapter.prompt_multi_select.assert_called_once()


class TypedBridge(UXBridge):
    """Bridge that records progress interactions for typed workflow tests."""

    def __init__(self) -> None:
        self.messages: list[str] = []
        self.progress_updates: list[str] = []

    def ask_question(self, *args, **kwargs) -> str:  # pragma: no cover - not used
        raise AssertionError("ask_question should not be called in typed bridge test")

    def confirm_choice(self, *args, **kwargs) -> bool:  # pragma: no cover
        raise AssertionError("confirm_choice should not be called in typed bridge test")

    def display_result(
        self, message: str, *, highlight: bool = False, message_type: str | None = None
    ) -> None:
        self.messages.append(message)

    def create_progress(self, description: str, *, total: int = 100):
        class _Indicator:
            def __init__(self, tracker: list[str]) -> None:
                self.tracker = tracker

            def update(self, **kwargs) -> None:
                self.tracker.append(kwargs.get("description", ""))

            def complete(self) -> None:  # pragma: no cover - no-op for tests
                pass

        return _Indicator(self.progress_updates)


@pytest.mark.fast
def test_setup_wizard_accepts_typed_inputs(tmp_path, monkeypatch) -> None:
    """The wizard accepts typed inputs without prompting."""

    monkeypatch.chdir(tmp_path)
    bridge = TypedBridge()
    constraints_path = tmp_path / "constraints.txt"
    selections = {
        "root": tmp_path,
        "structure": "single_package",
        "language": "python",
        "constraints": constraints_path,
        "goals": "typed goal",
        "memory_backend": "memory",
        "offline_mode": True,
        "features": {"code_generation": True, "test_generation": True},
        "auto_confirm": True,
    }

    wizard = SetupWizard(bridge)
    cfg = wizard.run(**selections)

    assert Path(cfg.config.project_root) == tmp_path
    assert cfg.config.constraints == str(constraints_path)
    assert cfg.config.features["code_generation"] is True
    assert any("Configuration Summary" in msg for msg in bridge.messages)
