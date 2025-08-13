import json
from pathlib import Path
from unittest.mock import MagicMock

import yaml

from devsynth.application.cli.config import CLIConfig
from devsynth.application.requirements.wizard import requirements_wizard
from devsynth.interface.ux_bridge import UXBridge


def test_priority_and_constraints_persist_after_navigation(tmp_path, monkeypatch):
    """User selections persist when navigating backwards."""
    monkeypatch.chdir(tmp_path)
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
