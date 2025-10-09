"""Regression coverage for the typed dialectical reasoning workflow."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from devsynth.domain.models.wsde_dialectical import DialecticalSequence
from devsynth.domain.models.wsde_dialectical_types import DialecticalTask
from devsynth.domain.models.wsde_facade import WSDETeam
from tests.helpers import DialecticalTaskFactory


class MemoryRecorder:
    """Memory stub capturing typed dialectical interactions."""

    def __init__(self) -> None:
        self.calls: list[tuple[DialecticalTask, DialecticalSequence]] = []

    def store_dialectical_result(
        self, task: DialecticalTask, result: DialecticalSequence
    ) -> None:
        self.calls.append((task, result))


@pytest.mark.fast
def test_apply_dialectical_reasoning_invokes_hooks_and_memory() -> None:
    """End-to-end reasoning returns typed artefacts and integrates hooks."""

    team = WSDETeam(name="workflow-regression")
    task_factory = DialecticalTaskFactory()
    task = task_factory.build(
        solution={
            "content": "Short solution lacking examples.",
            "code": "print('hello world')",
        }
    )

    critic = SimpleNamespace(name="critic-agent")
    memory = MemoryRecorder()
    hook_calls: list[tuple[DialecticalTask, tuple[DialecticalSequence, ...]]] = []

    def hook(task_payload: DialecticalTask, sequences: tuple[DialecticalSequence, ...]):
        hook_calls.append((task_payload, sequences))

    team.register_dialectical_hook(hook)

    result = team.apply_dialectical_reasoning(task, critic, memory_integration=memory)

    assert isinstance(result, DialecticalSequence)
    serialized = result.to_dict()
    assert serialized["status"] == "completed"
    assert serialized["synthesis"]

    assert hook_calls, "Hook should be invoked with the generated sequence"
    hook_task, hook_sequences = hook_calls[0]
    assert isinstance(hook_task, DialecticalTask)
    assert hook_task.identifier == task.identifier
    assert hook_sequences[0] is result

    assert memory.calls
    recorded_task, recorded_sequence = memory.calls[0]
    assert recorded_task.identifier == task.identifier
    assert recorded_sequence is result


@pytest.mark.fast
def test_dialectical_task_serialization_round_trip() -> None:
    """Tasks convert cleanly between mappings and typed wrappers."""

    payload = {
        "id": "task-123",
        "solution": {"content": "Original"},
        "metadata": {"priority": "high"},
    }

    task = DialecticalTask.from_mapping(payload)
    assert task.identifier == "task-123"
    assert task.metadata["priority"] == "high"

    updated = task.with_solution({"content": "Updated"})
    assert updated["solution"] == {"content": "Updated"}
    assert updated.identifier == task.identifier

    assert updated.to_dict()["solution"] == {"content": "Updated"}
