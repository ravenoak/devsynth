"""Focused tests for the enhanced Agent API bridge helpers."""

from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

pytestmark = [pytest.mark.requires_resource("webui"), pytest.mark.fast]


@pytest.fixture
def enhanced_module():
    """Reload the enhanced Agent API module for a pristine state."""

    import devsynth.interface.agentapi_enhanced as agentapi_enhanced

    importlib.reload(agentapi_enhanced)
    agentapi_enhanced.reset_state()
    return agentapi_enhanced


def test_api_bridge_answers_and_defaults(enhanced_module):
    """Scripted answers are consumed before falling back to defaults."""

    bridge = enhanced_module.APIBridge(["YES"])
    assert bridge.ask_question("Question?", choices=["alpha", "beta"]) == "YES"
    assert "Question?" in bridge.messages[0]

    # When answers are exhausted the first choice is used.
    assert bridge.ask_question("Next?", choices=["first", "second"]) == "first"
    assert "Next?" in bridge.messages[1]


def test_api_bridge_confirm_choice_coerces_booleans(enhanced_module):
    """Boolean prompts accept flexible truthy/falsey responses."""

    bridge = enhanced_module.APIBridge(["TrUe"])
    assert bridge.confirm_choice("Confirm?", default=False) is True
    assert "Confirm?" in bridge.messages[0]

    # Without scripted answers the default is returned but still recorded.
    assert bridge.confirm_choice("Again?", default=True) is True
    assert bridge.messages[-1].endswith("Again?")


def test_enhanced_progress_tracks_subtasks(enhanced_module):
    """Progress helper captures task state and validates subtask IDs."""

    bridge = enhanced_module.APIBridge()
    progress = bridge.create_progress("Build", total=4)

    progress.update(advance=1)
    task_id = progress.add_subtask("Sub", total=2)
    progress.update_subtask(task_id, advance=1)

    with pytest.raises(ValueError):
        progress.update_subtask("unknown")

    progress.complete_subtask(task_id)
    progress.complete()

    assert bridge.messages[0] == "Starting: Build (0/4)"
    assert any(
        "Progress: Build (1/4) - Processing..." in msg for msg in bridge.messages
    )
    assert any("Subtask started: Sub" in msg for msg in bridge.messages)
    assert any("Subtask progress: Sub" in msg for msg in bridge.messages)
    assert any("Subtask completed: Sub" in msg for msg in bridge.messages)
    assert bridge.messages[-1] == "Completed: Build"


def test_enhanced_rate_limit_blocks_abusive_clients(enhanced_module):
    """Rate limiting mirrors the base implementation for consistency."""

    request = SimpleNamespace(client=SimpleNamespace(host="10.0.0.5"))
    state = enhanced_module.reset_state()
    state.rate_limiter.buckets["10.0.0.5"] = [1.0, 2.0]
    with pytest.raises(enhanced_module.HTTPException) as exc:
        enhanced_module.rate_limit(
            request,
            limit=2,
            window=60,
            state=state,
            current_time=3.0,
        )

    assert exc.value.status_code == enhanced_module.status.HTTP_429_TOO_MANY_REQUESTS
