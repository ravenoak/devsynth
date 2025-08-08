import os
import sys
from types import ModuleType

import yaml

# Ensures gather_requirements persists priority, goals, and constraints

# Stub optional heavy dependencies for test isolation
for _name in [
    "langgraph",
    "langgraph.checkpoint",
    "langgraph.checkpoint.base",
    "langgraph.graph",
    "tiktoken",
    "duckdb",
    "lmdb",
    "faiss",
    "httpx",
]:
    if _name not in sys.modules:
        _mod = ModuleType(_name)
        if _name == "langgraph.checkpoint.base":
            _mod.BaseCheckpointSaver = object
            _mod.empty_checkpoint = object()
        if _name == "langgraph.graph":
            _mod.END = None
            _mod.StateGraph = object
        if _name == "tiktoken":
            _mod.encoding_for_model = lambda *a, **k: None
        sys.modules[_name] = _mod

from devsynth.application.requirements.interactions import gather_requirements


def test_gather_updates_config_succeeds(tmp_path, monkeypatch):
    """Test that gather updates config succeeds.

    ReqID: N/A"""
    os.chdir(tmp_path)
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))
    os.makedirs(".devsynth", exist_ok=True)
    with open(".devsynth/project.yaml", "w", encoding="utf-8") as f:
        f.write("{}")
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
    output = tmp_path / "requirements_plan.yaml"
    gather_requirements(bridge, output_file=str(output))

    cfg_path = tmp_path / ".devsynth" / "project.yaml"
    data = yaml.safe_load(open(cfg_path, encoding="utf-8"))
    assert data.get("priority") == "high"
    assert data.get("goals") == "goal1"
    assert data.get("constraints") == "constraint1"

    plan = yaml.safe_load(open(output, encoding="utf-8"))
    assert plan["priority"] == "high"
    assert plan["goals"] == ["goal1"]
    assert plan["constraints"] == ["constraint1"]
