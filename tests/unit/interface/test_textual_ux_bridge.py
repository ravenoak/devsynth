"""Tests for the Textual UX bridge abstraction."""

from __future__ import annotations

import pytest

from devsynth.interface.textual_ui import MultiPaneLayout, TextualUXBridge


@pytest.mark.fast
def test_question_and_display_interactions_are_recorded() -> None:
    layout = MultiPaneLayout.default()
    bridge = TextualUXBridge(
        question_responses=["answer"],
        confirm_responses=[True],
        layout=layout,
    )

    response = bridge.ask_question("What <option>?", choices=["A", "B"], default="B")
    assert response == "answer"
    assert "What &lt;option&gt;?" in layout.content.lines[-1]
    assert "A" in layout.sidebar.lines[-1]

    bridge.display_result("Completed <success>", highlight=True, message_type="success")

    history = bridge.interaction_history
    assert history[0]["response"] == "answer"
    assert history[-1]["message"] == "Completed &lt;success&gt;"
    assert layout.log.lines[-1] == "Completed &lt;success&gt;"


@pytest.mark.fast
def test_confirm_choice_falls_back_to_default() -> None:
    bridge = TextualUXBridge(confirm_responses=[])

    assert bridge.confirm_choice("Proceed?", default=True) is True
    assert bridge.confirm_choice("Stop?", default=False) is False


@pytest.mark.fast
def test_progress_updates_capture_nested_subtasks() -> None:
    bridge = TextualUXBridge()
    indicator = bridge.create_progress("Main Task", total=10)
    indicator.update(advance=4, status="Processing...")

    subtask_id = indicator.add_subtask("Phase 1", total=5)
    indicator.update_subtask(subtask_id, advance=3, status="Almost done...")
    nested_id = indicator.add_nested_subtask(subtask_id, "Phase 1.a", total=2)
    indicator.update_nested_subtask(parent_id=subtask_id, task_id=nested_id, advance=2)
    indicator.complete_nested_subtask(subtask_id, nested_id)
    indicator.complete_subtask(subtask_id)
    indicator.complete()

    snapshots = bridge.progress_snapshots
    assert snapshots[-1]["status"] == "Complete"
    assert snapshots[-1]["current"] == 10.0
    nested = snapshots[-1]["nested_subtasks"][subtask_id]
    assert nested["status"] == "Complete"
    assert nested["nested_subtasks"][nested_id]["status"] == "Complete"


@pytest.mark.fast
def test_capabilities_reflect_textual_availability() -> None:
    bridge = TextualUXBridge()
    caps = bridge.capabilities
    assert caps["supports_progress_updates"] is True
    if TextualUXBridge.is_textual_available():
        assert caps["supports_layout_panels"] is True
    else:
        assert caps["supports_layout_panels"] is False


@pytest.mark.fast
def test_require_textual_guard() -> None:
    if TextualUXBridge.is_textual_available():
        pytest.skip("Textual is installed; guard is not expected to trigger.")

    with pytest.raises(RuntimeError):
        TextualUXBridge(require_textual=True)
