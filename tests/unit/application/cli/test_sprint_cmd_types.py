from __future__ import annotations

import json
from pathlib import Path

import pytest

from devsynth.application.cli import sprint_cmd


@pytest.mark.fast
def test_sprint_planning_cmd_returns_structured_plan(tmp_path: Path) -> None:
    """The sprint planning helper returns a typed dictionary."""

    payload = {
        "recommended_scope": ["story-123"],
        "objectives": ["ship"],
        "success_criteria": ["tests green"],
    }
    source = tmp_path / "requirements.json"
    source.write_text(json.dumps(payload))

    plan = sprint_cmd.sprint_planning_cmd(str(source))

    assert plan["planned_scope"] == payload["recommended_scope"]
    assert plan["objectives"] == payload["objectives"]
    assert plan["success_criteria"] == payload["success_criteria"]


@pytest.mark.fast
def test_sprint_retrospective_cmd_defaults_when_missing(tmp_path: Path) -> None:
    """The retrospective helper always returns structured fields."""

    summary = sprint_cmd.sprint_retrospective_cmd("{}", sprint=5)
    assert summary["positives"] == []
    assert summary["improvements"] == []
    assert summary["action_items"] == []
    assert summary["sprint"] == 5


@pytest.mark.fast
def test_sprint_retrospective_cmd_handles_invalid_json() -> None:
    """Gracefully handle non-JSON input by returning empty structures."""

    summary = sprint_cmd.sprint_retrospective_cmd("not-json", sprint=7)
    assert summary["positives"] == []
    assert summary["sprint"] == 7
