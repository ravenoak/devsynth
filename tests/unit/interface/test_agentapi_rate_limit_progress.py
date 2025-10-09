"""Unit tests for Agent API rate limiting and progress tracking."""

from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

pytestmark = [pytest.mark.requires_resource("webui"), pytest.mark.fast]


@pytest.fixture
def agentapi_module():
    """Reload the module to ensure clean global state between tests."""

    import devsynth.interface.agentapi as agentapi

    importlib.reload(agentapi)
    agentapi.REQUEST_TIMESTAMPS.clear()
    agentapi.LATEST_MESSAGES.clear()
    return agentapi


def test_rate_limit_allows_after_window(agentapi_module, monkeypatch):
    """Old requests outside the window are discarded before counting."""

    request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))
    monkeypatch.setattr(agentapi_module.time, "time", lambda: 100.0)

    agentapi_module.rate_limit(request, limit=2, window=60)
    assert agentapi_module.REQUEST_TIMESTAMPS["127.0.0.1"] == [100.0]

    monkeypatch.setattr(agentapi_module.time, "time", lambda: 170.0)
    agentapi_module.rate_limit(request, limit=2, window=60)
    assert agentapi_module.REQUEST_TIMESTAMPS["127.0.0.1"] == [170.0]


def test_rate_limit_raises_when_exceeded(agentapi_module, monkeypatch):
    """Clients exceeding the limit receive a HTTP 429 error."""

    request = SimpleNamespace(client=SimpleNamespace(host="8.8.8.8"))
    agentapi_module.REQUEST_TIMESTAMPS["8.8.8.8"] = [10.0, 20.0]
    monkeypatch.setattr(agentapi_module.time, "time", lambda: 30.0)

    with pytest.raises(agentapi_module.HTTPException) as exc:
        agentapi_module.rate_limit(request, limit=2, window=60)

    assert exc.value.status_code == agentapi_module.status.HTTP_429_TOO_MANY_REQUESTS


def test_api_bridge_progress_records_subtasks(agentapi_module):
    """The progress helper emits clear messages for tasks and subtasks."""

    bridge = agentapi_module.APIBridge()
    progress = bridge.create_progress("Task", total=4)

    progress.update(advance=1)
    progress.update(advance=1, status="Half done")

    task_id = progress.add_subtask("Subtask", total=2)
    progress.update_subtask(task_id, advance=1)

    snapshot = list(bridge.messages)
    progress.update_subtask("missing")
    assert bridge.messages == snapshot

    progress.complete_subtask(task_id)
    progress.complete()

    assert bridge.messages[0] == "Task"
    assert bridge.messages[1] == "Task (1/4) - Starting..."
    assert any(message.endswith("- Half done") for message in bridge.messages)
    assert any(message.strip().startswith("↳ Subtask") for message in bridge.messages)
    assert any("(1/2)" in message for message in bridge.messages)
    assert any(
        message.strip().endswith("Subtask complete") for message in bridge.messages
    )
    assert bridge.messages[-1] == "Task complete"


def test_api_bridge_progress_normalizes_string_advances(agentapi_module):
    """String increments are coerced to floats and invalid entries ignored."""

    bridge = agentapi_module.APIBridge()
    progress = bridge.create_progress("Task", total=4)

    progress.update(advance="1")
    assert bridge.messages[1].startswith("Task (1/4)")

    subtask_id = progress.add_subtask("Subtask", total=2)
    progress.update_subtask(subtask_id, advance="1")
    assert any("Subtask (1/2)" in message for message in bridge.messages)

    nested_id = progress.add_nested_subtask(subtask_id, "Nested", total=2)
    progress.update_nested_subtask(subtask_id, nested_id, advance="1")
    assert any("Nested (1/2)" in message for message in bridge.messages)

    previous_messages = tuple(bridge.messages)
    progress.update(advance="invalid")
    assert bridge.messages[-1].startswith("Task (1/4)")
    assert len(bridge.messages) == len(previous_messages) + 1
