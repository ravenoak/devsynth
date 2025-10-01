import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from devsynth.application.cli.config import CLIConfig
from devsynth.application.requirements import wizard as wizard_mod
from devsynth.application.requirements.wizard import requirements_wizard
from devsynth.interface.ux_bridge import UXBridge

pytestmark = [pytest.mark.fast]


def test_priority_and_constraints_persist_after_navigation(tmp_path, monkeypatch):
    """User selections persist when navigating backwards."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        wizard_mod,
        "ensure_path_exists",
        lambda path, create=True: str(Path(path).resolve()),
    )
    responses = iter(
        [
            "Title",  # title
            "Desc",  # description
            "functional",  # type
            "high",  # priority initial
            "back",  # navigate back from constraints
            "low",  # updated priority
            "cpu,gpu",  # constraints
        ]
    )

    bridge = MagicMock(spec=UXBridge)
    bridge.ask_question.side_effect = lambda *args, **kwargs: next(responses)
    bridge.display_result = MagicMock()

    requirements_wizard(bridge, output_file="req.json", config=CLIConfig())

    data = json.loads(Path("req.json").read_text())
    assert data["priority"] == "low"
    assert data["constraints"] == ["cpu", "gpu"]

    project_yaml = Path(".devsynth/project.yaml")
    cfg_data = yaml.safe_load(project_yaml.read_text())
    assert cfg_data["priority"] == "low"
    assert cfg_data["constraints"] == "cpu,gpu"


def test_requirements_wizard_logs_each_step(monkeypatch, tmp_path):
    """Wizard steps emit structured log entries for auditing."""

    monkeypatch.chdir(tmp_path)

    logged = []

    class StubLogger:
        def info(self, message: str, **kwargs) -> None:
            logged.append((message, kwargs))

        def error(self, message: str, **kwargs) -> None:  # pragma: no cover - not used
            raise AssertionError("error logging was not expected")

    monkeypatch.setattr(wizard_mod, "DevSynthLogger", lambda name: StubLogger())

    class DummyConfig:
        priority = "medium"
        constraints = ""

    monkeypatch.setattr(wizard_mod, "get_project_config", lambda _path: DummyConfig())
    monkeypatch.setattr(wizard_mod, "save_config", lambda cfg, *, use_pyproject: None)

    class Bridge(UXBridge):
        def __init__(self) -> None:
            self._answers = iter(
                [
                    "Title",
                    "Description",
                    "functional",
                    "high",
                    "a,b",
                ]
            )

        def ask_question(self, *_a, **_k) -> str:
            return next(self._answers)

        def confirm_choice(self, *_a, **_k) -> bool:
            return True

        def display_result(self, *_a, **_k) -> None:
            pass

    requirements_wizard(Bridge(), config=CLIConfig())

    steps = {
        entry[1]["step"]: entry[1]["value"]
        for entry in logged
        if entry[0] == "wizard_step"
    }
    assert steps == {
        "title": "Title",
        "description": "Description",
        "type": "functional",
        "priority": "high",
        "constraints": "a,b",
    }


def test_requirements_wizard_logs_exc_info(monkeypatch, tmp_path):
    """Failures during save emit an error log with ``exc_info``."""

    monkeypatch.chdir(tmp_path)

    class StubLogger:
        def __init__(self) -> None:
            self.error_calls: list[dict[str, object]] = []

        def info(self, *_a, **_k) -> None:
            pass

        def error(self, message: str, **kwargs) -> None:
            self.error_calls.append({"message": message, **kwargs})

    stub_logger = StubLogger()
    monkeypatch.setattr(wizard_mod, "DevSynthLogger", lambda name: stub_logger)

    class DummyConfig:
        priority = "medium"
        constraints = ""

    monkeypatch.setattr(wizard_mod, "get_project_config", lambda _path: DummyConfig())

    def failing_save(_cfg, *, use_pyproject: bool) -> None:
        raise RuntimeError("disk full")

    monkeypatch.setattr(wizard_mod, "save_config", failing_save)

    class Bridge(UXBridge):
        def ask_question(self, *_a, **_k) -> str:
            return "value"

        def confirm_choice(self, *_a, **_k) -> bool:
            return True

        def display_result(self, *_a, **_k) -> None:
            pass

    with pytest.raises(RuntimeError, match="disk full"):
        requirements_wizard(Bridge(), config=CLIConfig())

    assert stub_logger.error_calls
    error_call = stub_logger.error_calls[0]
    assert error_call["message"] == "requirements_save_failed"
    assert isinstance(error_call["exc_info"], RuntimeError)
