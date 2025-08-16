import types

import pytest
from rich.console import Console

from devsynth.interface.cli import CLIProgressIndicator


class BadStr:
    def __str__(self) -> str:  # pragma: no cover - deliberately bad
        raise TypeError("bad string")


@pytest.mark.fast
def test_progress_indicator_init_with_bad_description_uses_fallback(caplog):
    """Ensure CLIProgressIndicator falls back when description conversion fails.

    ReqID: N/A"""
    console = Console()
    with caplog.at_level("WARNING"):
        indicator = CLIProgressIndicator(console, BadStr(), total=1)
    task = indicator._progress.tasks[indicator._task]
    assert task.description == "<main task>"
    assert any(
        "Failed to sanitize main task description" in rec.message
        for rec in caplog.records
    )


@pytest.mark.fast
def test_progress_indicator_update_with_bad_inputs_uses_fallback(caplog):
    """Ensure update handles bad description and status.

    ReqID: N/A"""
    indicator = CLIProgressIndicator(Console(), "task", total=1)
    with caplog.at_level("WARNING"):
        indicator.update(description=BadStr())
    task = indicator._progress.tasks[indicator._task]
    assert task.description == "<description>"
    assert any(
        "Failed to sanitize task description" in rec.message for rec in caplog.records
    )
    caplog.clear()
    with caplog.at_level("WARNING"):
        indicator.update(status=BadStr())
    task = indicator._progress.tasks[indicator._task]
    assert task.fields["status"] == "In progress..."
    assert any(
        "Failed to sanitize task status" in rec.message for rec in caplog.records
    )


@pytest.mark.fast
def test_progress_indicator_subtasks_with_bad_inputs_use_fallbacks(caplog):
    """Ensure subtask helpers handle malformed inputs gracefully.

    ReqID: N/A"""
    indicator = CLIProgressIndicator(Console(), "task", total=1)
    indicator._progress.live = types.SimpleNamespace(
        refresh=lambda *args, **kwargs: None, is_started=False
    )
    caplog.set_level("WARNING")
    sub_id = indicator.add_subtask(BadStr())
    assert indicator._progress.tasks[sub_id].description == "  ↳ <subtask>"
    assert any(
        "Failed to sanitize subtask description" in rec.message
        for rec in caplog.records
    )
    caplog.clear()
    indicator.update_subtask(sub_id, description=BadStr())
    assert indicator._progress.tasks[sub_id].description == "  ↳ <description>"
    assert any(
        "Failed to sanitize subtask update description" in rec.message
        for rec in caplog.records
    )
    caplog.clear()
    indicator.update_subtask(sub_id, status=BadStr())
    assert indicator._progress.tasks[sub_id].fields["status"] == "In progress..."
    assert any(
        "Failed to sanitize subtask status" in rec.message for rec in caplog.records
    )
    caplog.clear()
    nested_id = indicator.add_nested_subtask(sub_id, BadStr())
    assert indicator._progress.tasks[nested_id].description == "    ↳ <nested subtask>"
    assert any(
        "Failed to sanitize nested subtask description" in rec.message
        for rec in caplog.records
    )
    caplog.clear()
    indicator.update_nested_subtask(sub_id, nested_id, description=BadStr())
    assert indicator._progress.tasks[nested_id].description == "    ↳ <description>"
    assert any(
        "Failed to sanitize nested subtask update description" in rec.message
        for rec in caplog.records
    )
    caplog.clear()
    indicator.update_nested_subtask(sub_id, nested_id, status=BadStr())
    assert indicator._progress.tasks[nested_id].fields["status"] == "In progress..."
    assert any(
        "Failed to sanitize nested subtask status" in rec.message
        for rec in caplog.records
    )
