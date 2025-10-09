"""Tests covering progress helper types exposed by UX bridge."""

from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest


class _FakePasswordHasher:
    def __init__(
        self, *args: object, **kwargs: object
    ) -> None:  # pragma: no cover - simple stub
        pass

    def hash(self, password: str) -> str:  # pragma: no cover - simple stub
        return password

    def verify(
        self, stored_hash: str, password: str
    ) -> bool:  # pragma: no cover - simple stub
        return stored_hash == password


sys.modules.setdefault("argon2", SimpleNamespace(PasswordHasher=_FakePasswordHasher))
sys.modules.setdefault(
    "argon2.exceptions", SimpleNamespace(VerifyMismatchError=Exception)
)


from devsynth.interface.ux_bridge import (
    PROGRESS_STATUS_VALUES,
    ProgressIndicator,
    SubtaskProgressSnapshot,
    SupportsNestedSubtasks,
    UXBridge,
)


class _TestBridge(UXBridge):
    """Minimal bridge to access the internal dummy progress indicator."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def ask_question(
        self,
        message: str,
        *,
        choices: tuple[str, ...] | None = None,
        default: str | None = None,
        show_default: bool = True,
    ) -> str:
        return default or (choices[0] if choices else "")

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        return default

    def display_result(
        self,
        message: str,
        *,
        highlight: bool = False,
        message_type: str | None = None,
    ) -> None:
        self.messages.append(message)


@pytest.mark.fast
def test_dummy_progress_supports_nested_protocol() -> None:
    """The built-in dummy progress indicator exposes nested operations."""

    indicator = _TestBridge().create_progress("task")
    assert isinstance(indicator, ProgressIndicator)
    assert isinstance(indicator, SupportsNestedSubtasks)

    subtask_id = indicator.add_subtask("child", status=PROGRESS_STATUS_VALUES[0])
    nested_id = indicator.add_nested_subtask(subtask_id, "nested")
    indicator.update_subtask(subtask_id, status=PROGRESS_STATUS_VALUES[1])
    indicator.update_nested_subtask(
        subtask_id, nested_id, status=PROGRESS_STATUS_VALUES[2]
    )
    indicator.complete_nested_subtask(subtask_id, nested_id)
    indicator.complete_subtask(subtask_id)
    indicator.complete()


@pytest.mark.fast
def test_subtask_snapshot_typed_structure() -> None:
    """Subtask snapshots allow the expected progress fields."""

    snapshot: SubtaskProgressSnapshot = {
        "description": "Example",
        "total": 100.0,
        "current": 10.0,
        "status": PROGRESS_STATUS_VALUES[0],
        "nested_subtasks": {},
    }

    assert snapshot["status"] == PROGRESS_STATUS_VALUES[0]
