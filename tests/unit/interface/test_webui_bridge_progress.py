"""Behavioral tests for WebUI progress tracking utilities."""

from __future__ import annotations

import importlib
from typing import List, Set

import pytest

from devsynth.exceptions import DevSynthError
from devsynth.interface import webui_bridge


pytestmark = pytest.mark.fast


class _SanitizeSpy:
    """Callable spy that tracks sanitize invocations and supports failures."""

    def __init__(self) -> None:
        self.calls: List[str] = []
        self.fail_on: Set[str] = set()

    def __call__(self, value: str) -> str:
        self.calls.append(value)
        if value in self.fail_on:
            raise ValueError("sanitize failure for testing")
        return f"sanitized::{value}"


@pytest.fixture()
def sanitize_spy(monkeypatch: pytest.MonkeyPatch) -> _SanitizeSpy:
    spy = _SanitizeSpy()
    monkeypatch.setattr(webui_bridge, "sanitize_output", spy)
    return spy


def _assert_default_status_cycle(indicator: webui_bridge.WebUIProgressIndicator) -> None:
    """Advance ``indicator`` through threshold updates asserting status text."""

    indicator.update(advance=15)
    assert indicator._status == "Starting..."

    indicator.update(advance=0)
    assert indicator._status == "Processing..."

    indicator.update(advance=25)
    indicator.update(advance=0)
    assert indicator._status == "Halfway there..."

    indicator.update(advance=25)
    indicator.update(advance=0)
    assert indicator._status == "Almost done..."

    indicator.update(advance=24)
    indicator.update(advance=0)
    assert indicator._status == "Finalizing..."

    indicator.update(advance=1)
    indicator.update(advance=0)
    assert indicator._status == "Complete"


def test_progress_indicator_update_paths(sanitize_spy: _SanitizeSpy) -> None:
    """``update`` sanitizes supplied text and cycles default status thresholds."""

    indicator = webui_bridge.WebUIProgressIndicator("initial", 100)

    indicator.update(description="desc-1", status="status-1", advance=10)
    assert sanitize_spy.calls[:2] == ["desc-1", "status-1"]
    assert indicator._description == "sanitized::desc-1"
    assert indicator._status == "sanitized::status-1"

    indicator.update(description="desc-2", advance=0)
    assert sanitize_spy.calls[2] == "desc-2"
    assert indicator._description == "sanitized::desc-2"
    assert indicator._status == "Starting..."

    indicator.update(status="status-2", advance=0)
    assert sanitize_spy.calls[3] == "status-2"
    assert indicator._status == "sanitized::status-2"

    indicator.update(description="desc-3", status="status-3", advance=0)
    assert sanitize_spy.calls[4:6] == ["desc-3", "status-3"]
    assert indicator._description == "sanitized::desc-3"
    assert indicator._status == "sanitized::status-3"

    _assert_default_status_cycle(indicator)
    assert sanitize_spy.calls == [
        "desc-1",
        "status-1",
        "desc-2",
        "status-2",
        "desc-3",
        "status-3",
    ]


def test_progress_indicator_subtasks_and_nested_operations(
    sanitize_spy: _SanitizeSpy,
) -> None:
    """Subtask lifecycle sanitizes text, handles fallbacks, and ignores invalid IDs."""

    indicator = webui_bridge.WebUIProgressIndicator("main", 100)

    task_id = indicator.add_subtask("alpha", total=10)
    assert sanitize_spy.calls[-1] == "alpha"
    assert indicator._subtasks[task_id]["description"] == "sanitized::alpha"

    indicator.update_subtask(task_id, advance=2, description="beta")
    assert sanitize_spy.calls[-1] == "beta"
    assert indicator._subtasks[task_id]["current"] == 2
    assert indicator._subtasks[task_id]["description"] == "sanitized::beta"

    sanitize_spy.fail_on.add("bad-desc")
    indicator.update_subtask(task_id, description="bad-desc")
    assert indicator._subtasks[task_id]["description"] == "sanitized::beta"
    sanitize_spy.fail_on.remove("bad-desc")

    before = list(sanitize_spy.calls)
    indicator.update_subtask("missing", description="gamma")
    assert sanitize_spy.calls == before

    nested_id = indicator.add_nested_subtask(task_id, "nested", total=4, status="init")
    assert sanitize_spy.calls[-1] == "nested"
    nested = indicator._subtasks[task_id]["nested_subtasks"][nested_id]
    assert nested["description"] == "sanitized::nested"
    assert nested["status"] == "init"

    indicator.update_nested_subtask(
        task_id, nested_id, advance=1, description="n-desc", status="n-status"
    )
    assert sanitize_spy.calls[-2:] == ["n-desc", "n-status"]
    nested = indicator._subtasks[task_id]["nested_subtasks"][nested_id]
    assert nested["current"] == 1
    assert nested["description"] == "sanitized::n-desc"
    assert nested["status"] == "sanitized::n-status"

    sanitize_spy.fail_on.add("bad-status")
    indicator.update_nested_subtask(task_id, nested_id, status="bad-status")
    nested = indicator._subtasks[task_id]["nested_subtasks"][nested_id]
    assert nested["status"] == "In progress..."
    sanitize_spy.fail_on.remove("bad-status")

    before = list(sanitize_spy.calls)
    indicator.update_nested_subtask("missing", nested_id, description="skip")
    indicator.update_nested_subtask(task_id, "missing", description="skip")
    assert sanitize_spy.calls == before

    sanitize_spy.fail_on.add("fail-sub")
    fallback_id = indicator.add_subtask("fail-sub")
    assert indicator._subtasks[fallback_id]["description"] == "<subtask>"

    sanitize_spy.fail_on.add("fail-nested")
    fallback_nested = indicator.add_nested_subtask(fallback_id, "fail-nested")
    assert fallback_nested
    nested = indicator._subtasks[fallback_id]["nested_subtasks"][fallback_nested]
    assert nested["description"] == "<nested subtask>"

    missing_nested = indicator.add_nested_subtask("missing", "noop")
    assert missing_nested == ""

    indicator.complete_nested_subtask(task_id, nested_id)
    nested = indicator._subtasks[task_id]["nested_subtasks"][nested_id]
    assert nested["completed"] is True
    assert nested["current"] == nested["total"]
    assert nested["status"] == "Complete"

    pending_nested = indicator.add_nested_subtask(task_id, "pending")
    assert pending_nested
    assert sanitize_spy.calls[-1] == "pending"
    indicator.complete_subtask(task_id)
    subtask = indicator._subtasks[task_id]
    assert subtask["completed"] is True
    assert subtask["current"] == subtask["total"]
    for nested in subtask.get("nested_subtasks", {}).values():
        assert nested["completed"] is True
        assert nested["status"] == "Complete"

    indicator.complete_subtask("missing")
    indicator.complete_nested_subtask("missing", "missing")

    assert sanitize_spy.calls == [
        "alpha",
        "beta",
        "bad-desc",
        "nested",
        "n-desc",
        "n-status",
        "bad-status",
        "fail-sub",
        "fail-nested",
        "pending",
    ]


def test_require_streamlit_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """``_require_streamlit`` raises ``DevSynthError`` when import fails."""

    monkeypatch.setattr(webui_bridge, "st", None)
    seen = []

    def fake_import(name: str):
        seen.append(name)
        raise ImportError("no module named streamlit")

    monkeypatch.setattr(importlib, "import_module", fake_import)
    with pytest.raises(DevSynthError):
        webui_bridge._require_streamlit()
    assert seen == ["streamlit"]


def test_adjust_wizard_step_edges() -> None:
    """Edge cases clamp wizard step navigation within valid bounds."""

    adjust = webui_bridge.WebUIBridge.adjust_wizard_step

    assert adjust(0, direction="back", total=0) == 0
    assert adjust(0, direction="next", total=0) == 0
    assert adjust("2", direction="next", total=5) == 3
    assert adjust("abc", direction="back", total=3) == 0
    assert adjust(2, direction="back", total=5) == 1
    assert adjust(2, direction="next", total=3) == 2
    assert adjust(0, direction="back", total=3) == 0
    assert adjust(1, direction="next", total=2.5) == 0
    assert adjust(1, direction="stay", total=2) == 1
