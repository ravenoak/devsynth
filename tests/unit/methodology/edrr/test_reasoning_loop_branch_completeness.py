from __future__ import annotations

import importlib
import random
from collections.abc import Mapping
from typing import Any

import pytest

import devsynth.methodology.edrr.reasoning_loop as rl
from devsynth.domain.models.wsde_dialectical import DialecticalSequence
from devsynth.methodology.edrr.contracts import CoordinatorRecorder, NullWSDETeam


class _MappingPayload(Mapping[str, Any]):
    """Lightweight mapping to validate dict-copy behavior."""

    def __init__(self, data: dict[str, Any]):
        self._data = data

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:  # pragma: no cover - len isn't called in test
        return len(self._data)


@pytest.mark.fast
def test_import_accessor_returns_typed_apply(monkeypatch):
    """The accessor surfaces the typed apply helper for default usage."""

    sentinel = object()
    monkeypatch.setattr(rl, "typed_apply", sentinel)

    assert rl._import_apply_dialectical_reasoning() is sentinel


@pytest.mark.fast
def test_import_accessor_default_path_executes() -> None:
    """Default accessor call exercises the module import helper."""

    assert callable(rl._import_apply_dialectical_reasoning())


@pytest.mark.fast
def test_dialectical_sequence_records_with_coordinator_fallback(monkeypatch):
    """DialecticalSequence payloads trigger coordinator fallback handling."""

    sequence = DialecticalSequence(sequence_id="seq-1", steps=(), status="completed")
    sequence._payload["phase"] = "mystery"
    sequence._payload["next_phase"] = "???"

    coordinator = CoordinatorRecorder()

    monkeypatch.setattr(
        rl, "_import_apply_dialectical_reasoning", lambda: lambda *_args, **_kwargs: sequence
    )

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "dialectical"},
        critic_agent=None,
        coordinator=coordinator,
    )

    assert results == [sequence]
    assert results[0] is sequence
    assert coordinator.records and coordinator.records[0][0] == "refine"
    assert coordinator.records[0][1]["phase"] == "mystery"
    assert coordinator.records[0][1]["next_phase"] == "???"


@pytest.mark.fast
def test_reasoning_loop_tolerates_seed_failures(monkeypatch):
    """Random/numpy seed failures are ignored so the loop can continue."""

    def raise_seed(_value: int) -> None:
        raise RuntimeError("seed unavailable")

    monkeypatch.setattr(random, "seed", raise_seed)

    original_import_module = importlib.import_module

    def fake_import_module(name: str, package: str | None = None):
        if name == "numpy.random":
            raise RuntimeError("numpy missing")
        return original_import_module(name, package)  # pragma: no cover - other imports

    monkeypatch.setattr(importlib, "import_module", fake_import_module)

    monkeypatch.setattr(
        rl,
        "_import_apply_dialectical_reasoning",
        lambda: lambda *_args, **_kwargs: {"status": "completed"},
    )

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "seed"},
        critic_agent=None,
        deterministic_seed=123,
    )

    assert results == [{"status": "completed"}]


@pytest.mark.fast
def test_reasoning_loop_branch_trace_complete(monkeypatch, caplog):
    """Comprehensive branch harness exercises deterministic reasoning paths."""

    assert callable(rl._import_apply_dialectical_reasoning())

    with monkeypatch.context() as patcher:
        seed_calls: list[int] = []
        patcher.setattr(random, "seed", lambda value: seed_calls.append(value))

        class FakeNumpyRandom:
            def __init__(self) -> None:
                self.calls: list[int] = []

            def seed(self, value: int) -> None:
                self.calls.append(value)

        numpy_random = FakeNumpyRandom()
        original_import_module = importlib.import_module

        def import_numpy(name: str, package: str | None = None):
            if name == "numpy.random":
                return numpy_random
            return original_import_module(name, package)

        patcher.setattr(importlib, "import_module", import_numpy)
        patcher.setattr(
            rl,
            "_import_apply_dialectical_reasoning",
            lambda: lambda *_args, **_kwargs: {"status": "completed"},
        )

        rl.reasoning_loop(
            wsde_team=NullWSDETeam(),
            task={"problem": "seed-success"},
            critic_agent=None,
            deterministic_seed=11,
        )

        assert seed_calls == [11]
        assert numpy_random.calls == [11]

    with monkeypatch.context() as patcher:
        def raise_seed(_value: int) -> None:
            raise RuntimeError("seed unavailable")

        original_import_module = importlib.import_module

        def fail_numpy(name: str, package: str | None = None):
            if name == "numpy.random":
                raise RuntimeError("numpy missing")
            return original_import_module(name, package)

        patcher.setattr(random, "seed", raise_seed)
        patcher.setattr(importlib, "import_module", fail_numpy)
        patcher.setattr(
            rl,
            "_import_apply_dialectical_reasoning",
            lambda: lambda *_args, **_kwargs: {"status": "completed"},
        )

        assert (
            rl.reasoning_loop(
                wsde_team=NullWSDETeam(),
                task={"problem": "seed-failure"},
                critic_agent=None,
                deterministic_seed=13,
            )
            == [{"status": "completed"}]
        )

    with monkeypatch.context() as patcher:
        monotonic_values = iter([0.0, 0.2])
        patcher.setattr(rl.time, "monotonic", lambda: next(monotonic_values))
        patcher.setattr(
            rl,
            "_import_apply_dialectical_reasoning",
            lambda: lambda *_args, **_kwargs: {"status": "completed"},
        )

        assert (
            rl.reasoning_loop(
                wsde_team=NullWSDETeam(),
                task={"problem": "budget-guard"},
                critic_agent=None,
                max_total_seconds=0.1,
            )
            == []
        )

    with monkeypatch.context() as patcher:
        attempts = {"value": 0}

        def flaky(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            attempts["value"] += 1
            if attempts["value"] == 1:
                raise RuntimeError("transient")
            return {"status": "in_progress", "phase": "expand"}

        clock = {"value": 0.0}
        sleep_calls: list[float] = []

        def fake_monotonic() -> float:
            return clock["value"]

        def fake_sleep(duration: float) -> None:
            sleep_calls.append(duration)
            clock["value"] += duration

        patcher.setattr(rl, "_import_apply_dialectical_reasoning", lambda: flaky)
        patcher.setattr(rl.time, "monotonic", fake_monotonic)
        patcher.setattr(rl.time, "sleep", fake_sleep)

        caplog.set_level("DEBUG", rl.logger.logger.name)
        results = rl.reasoning_loop(
            wsde_team=NullWSDETeam(),
            task={"problem": "retry"},
            critic_agent=None,
            retry_attempts=1,
            retry_backoff=0.2,
            max_total_seconds=0.5,
            max_iterations=1,
        )

        assert results == [{"status": "in_progress", "phase": "expand"}]
        assert attempts["value"] == 2
        assert sleep_calls == [0.2]
        assert any("Transient error in reasoning step" in r.message for r in caplog.records)

    with monkeypatch.context() as patcher:
        call_counter = {"value": 0}

        def always_transient(*_args: Any, **_kwargs: Any) -> None:
            call_counter["value"] += 1
            raise RuntimeError("budget exhausted")

        times = iter([0.0, 0.05, 0.2])
        monotonic_history: list[float] = []

        def fake_monotonic_budget() -> float:
            try:
                value = next(times)
            except StopIteration:
                value = 0.2
            monotonic_history.append(value)
            return value

        sleep_calls: list[float] = []

        patcher.setattr(rl, "_import_apply_dialectical_reasoning", lambda: always_transient)
        patcher.setattr(rl.time, "monotonic", fake_monotonic_budget)
        patcher.setattr(rl.time, "sleep", lambda duration: sleep_calls.append(duration))

        assert (
            rl.reasoning_loop(
                wsde_team=NullWSDETeam(),
                task={"problem": "budget-clamp"},
                critic_agent=None,
                retry_attempts=2,
                retry_backoff=0.5,
                max_total_seconds=0.1,
            )
            == []
        )
        assert call_counter["value"] == 1
        assert sleep_calls == []
        assert monotonic_history == [0.0, 0.05, 0.2]

    with monkeypatch.context() as patcher:
        coordinator = CoordinatorRecorder()
        sequence = DialecticalSequence(sequence_id="seq", steps=(), status="completed")
        sequence._payload["phase"] = "mystery"
        sequence._payload["next_phase"] = "???"

        patcher.setattr(
            rl,
            "_import_apply_dialectical_reasoning",
            lambda: lambda *_args, **_kwargs: sequence,
        )

        results = rl.reasoning_loop(
            wsde_team=NullWSDETeam(),
            task={"problem": "sequence"},
            critic_agent=None,
            coordinator=coordinator,
        )

        assert results == [sequence]
        assert coordinator.records and coordinator.records[0][0] == "refine"

    with monkeypatch.context() as patcher:
        coordinator = CoordinatorRecorder()
        call_state = {"value": 0}

        class TaskStub:
            def __init__(self) -> None:
                self.syntheses: list[Any] = []

            def with_solution(self, synthesis: Any) -> "TaskStub":
                self.syntheses.append(synthesis)
                return self

        task_stub = TaskStub()

        def scripted(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            call_state["value"] += 1
            if call_state["value"] == 1:
                return {
                    "status": "in_progress",
                    "phase": "expand",
                    "next_phase": "differentiate",
                    "synthesis": {"content": "draft"},
                }
            if call_state["value"] == 2:
                return {
                    "status": "in_progress",
                    "phase": "differentiate",
                    "next_phase": "refine",
                }
            return {
                "status": "completed",
                "phase": "refine",
            }

        patcher.setattr(rl, "ensure_dialectical_task", lambda _task: task_stub)
        patcher.setattr(rl, "_import_apply_dialectical_reasoning", lambda: scripted)

        results = rl.reasoning_loop(
            wsde_team=NullWSDETeam(),
            task={"problem": "mapping"},
            critic_agent=None,
            coordinator=coordinator,
            phase=rl.Phase.EXPAND,
            max_iterations=3,
        )

        assert len(results) == 3
        assert task_stub.syntheses == [{"content": "draft"}]
        assert [record[0] for record in coordinator.records] == ["expand", "differentiate", "refine"]

    with monkeypatch.context() as patcher:
        patcher.setattr(
            rl,
            "_import_apply_dialectical_reasoning",
            lambda: lambda *_args, **_kwargs: 123,
        )

        with pytest.raises(TypeError):
            rl.reasoning_loop(
                wsde_team=NullWSDETeam(),
                task={"problem": "type-error"},
                critic_agent=None,
            )

    with monkeypatch.context() as patcher:
        patcher.setattr(
            rl,
            "_import_apply_dialectical_reasoning",
            lambda: lambda *_args, **_kwargs: {"status": "in_progress", "next_phase": "???"},
        )

        coordinator = CoordinatorRecorder()

        rl.reasoning_loop(
            wsde_team=NullWSDETeam(),
            task={"problem": "invalid-next"},
            critic_agent=None,
            coordinator=coordinator,
            phase=rl.Phase.DIFFERENTIATE,
            max_iterations=1,
        )

        assert coordinator.records == [
            (
                "differentiate",
                {"status": "in_progress", "next_phase": "???"},
            )
        ]

    with monkeypatch.context() as patcher:
        def always_transient_failure(*_args: Any, **_kwargs: Any) -> None:
            raise RuntimeError("retry exhaustion")

        patcher.setattr(rl, "_import_apply_dialectical_reasoning", lambda: always_transient_failure)

        caplog.set_level("DEBUG", rl.logger.logger.name)
        caplog.clear()

        results = rl.reasoning_loop(
            wsde_team=NullWSDETeam(),
            task={"problem": "retry-exhaust"},
            critic_agent=None,
            retry_attempts=0,
        )

        assert results == []
        assert any("Giving up after retries" in record.message for record in caplog.records)


@pytest.mark.fast
def test_reasoning_loop_configures_seed_providers(monkeypatch):
    """Successful seeding calls both random and numpy providers."""

    random_calls: list[int] = []

    def record_seed(value: int) -> None:
        random_calls.append(value)

    monkeypatch.setattr(random, "seed", record_seed)

    numpy_calls: list[int] = []

    class FakeNumpyRandom:
        def seed(self, value: int) -> None:
            numpy_calls.append(value)

    original_import_module = importlib.import_module

    def fake_import_module(name: str, package: str | None = None):
        if name == "numpy.random":
            return FakeNumpyRandom()
        return original_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", fake_import_module)

    monkeypatch.setattr(
        rl,
        "_import_apply_dialectical_reasoning",
        lambda: lambda *_args, **_kwargs: {"status": "completed"},
    )

    rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "seed"},
        critic_agent=None,
        deterministic_seed=99,
    )

    assert random_calls == [99]
    assert numpy_calls == [99]


@pytest.mark.fast
def test_reasoning_loop_budget_precheck(monkeypatch):
    """The total budget guard exits before invoking the dialectical step."""

    monotonic_values = iter([0.0, 0.2])

    def fake_monotonic() -> float:
        return next(monotonic_values)

    monkeypatch.setattr(rl.time, "monotonic", fake_monotonic)

    called = {"value": 0}

    def unexpected_call(
        *_args: Any, **_kwargs: Any
    ) -> dict[str, Any]:  # pragma: no cover - guard
        called["value"] += 1
        return {"status": "completed"}

    monkeypatch.setattr(
        rl, "_import_apply_dialectical_reasoning", lambda: unexpected_call
    )

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "budget"},
        critic_agent=None,
        max_total_seconds=0.1,
    )

    assert results == []
    assert called["value"] == 0


@pytest.mark.fast
def test_reasoning_loop_retry_retries_then_succeeds(monkeypatch):
    """Transient errors retry with backoff and then succeed."""

    attempts = {"value": 0}

    def flaky(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        attempts["value"] += 1
        if attempts["value"] == 1:
            raise RuntimeError("transient")
        return {"status": "completed"}

    sleep_calls: list[float] = []
    monkeypatch.setattr(rl.time, "sleep", lambda duration: sleep_calls.append(duration))
    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: flaky)

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "retry"},
        critic_agent=None,
        retry_attempts=1,
        retry_backoff=0.2,
    )

    assert attempts["value"] == 2
    assert sleep_calls == [0.2]
    assert results == [{"status": "completed"}]


@pytest.mark.fast
def test_reasoning_loop_retry_exhaustion_sets_stop(monkeypatch):
    """Exhausting retries triggers the stop flag and exits the loop."""

    def always_fail(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("boom")

    monkeypatch.setattr(rl.time, "sleep", lambda _duration: None)
    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: always_fail)

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "exhaust"},
        critic_agent=None,
        retry_attempts=0,
    )

    assert results == []


@pytest.mark.fast
def test_reasoning_loop_copies_mapping_payload(monkeypatch):
    """Mappings are materialized into dicts before storing results."""

    payload = _MappingPayload({"status": "completed", "phase": "refine"})

    monkeypatch.setattr(
        rl,
        "_import_apply_dialectical_reasoning",
        lambda: lambda *_args, **_kwargs: payload,
    )

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "mapping"},
        critic_agent=None,
    )

    assert results == [dict(payload)]
    assert results[0] is not payload


@pytest.mark.fast
def test_reasoning_loop_handles_dialectical_sequence(monkeypatch):
    """DialecticalSequence payloads propagate through coordinator fallbacks."""

    coordinator = CoordinatorRecorder()

    class TaskStub:
        def __init__(self) -> None:
            self.syntheses: list[dict[str, Any]] = []

        def with_solution(self, synthesis: dict[str, Any]) -> "TaskStub":
            self.syntheses.append(synthesis)
            return self

    task_stub = TaskStub()

    sequence = DialecticalSequence.from_dict(
        {
            "sequence_id": "seq-1",
            "status": "in_progress",
            "steps": [
                {
                    "id": "step-1",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "task_id": "task-1",
                    "thesis": {"content": "t"},
                    "antithesis": {
                        "id": "ant-1",
                        "timestamp": "2024-01-01T00:00:01Z",
                        "agent": "critic",
                        "critiques": [],
                        "critique_details": [],
                        "alternative_approaches": [],
                        "improvement_suggestions": [],
                    },
                    "synthesis": {"content": "s"},
                    "method": "dialectical_reasoning",
                }
            ],
        }
    )
    sequence._payload["phase"] = "unknown"
    sequence._payload["next_phase"] = None
    sequence._payload["synthesis"] = {"content": "s"}

    monkeypatch.setattr(rl, "ensure_dialectical_task", lambda _task: task_stub)
    monkeypatch.setattr(
        rl,
        "_import_apply_dialectical_reasoning",
        lambda: lambda *_args, **_kwargs: sequence,
    )

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "sequence"},
        critic_agent=None,
        coordinator=coordinator,
        phase=rl.Phase.REFINE,
        max_iterations=1,
    )

    assert results == [sequence]
    assert coordinator.records and coordinator.records[0][0] == "refine"
    recorded_payload = coordinator.records[0][1]
    assert recorded_payload["sequence_id"] == "seq-1"
    assert recorded_payload.get("synthesis", {"content": None})["content"] == "s"
    assert task_stub.syntheses == [{"content": "s"}]


@pytest.mark.fast
def test_reasoning_loop_raises_for_non_mapping_payload(monkeypatch):
    """Non-mapping results surface a TypeError guard."""

    monkeypatch.setattr(
        rl,
        "_import_apply_dialectical_reasoning",
        lambda: lambda *_args, **_kwargs: 42,
    )

    with pytest.raises(TypeError):
        rl.reasoning_loop(
            wsde_team=NullWSDETeam(),
            task={"problem": "oops"},
            critic_agent=None,
        )


@pytest.mark.fast
def test_reasoning_loop_halts_when_result_missing(monkeypatch):
    """A missing result terminates the loop without appending entries."""

    monkeypatch.setattr(
        rl,
        "_import_apply_dialectical_reasoning",
        lambda: lambda *_args, **_kwargs: None,
    )

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "void"},
        critic_agent=None,
        max_iterations=2,
    )

    assert results == []


@pytest.mark.fast
def test_reasoning_loop_branch_matrix(monkeypatch):
    """Exercise critical branches to raise module coverage above the release gate."""

    # Default accessor path (covers typed_apply import).
    with monkeypatch.context() as patcher:
        default_calls: list[Any] = []

        def default_apply(
            wsde_team: Any, task: Any, critic: Any, memory: Any
        ) -> dict[str, Any]:
            default_calls.append(task)
            return {"status": "completed", "phase": "refine"}

        patcher.setattr(rl, "typed_apply", default_apply)

        results = rl.reasoning_loop(
            wsde_team=NullWSDETeam(),
            task={"problem": "default"},
            critic_agent=None,
        )

        assert results == [{"status": "completed", "phase": "refine"}]
        assert default_calls

    # Deterministic seeding failures across random and numpy imports.
    with monkeypatch.context() as patcher:
        patcher.setattr(
            random,
            "seed",
            lambda _value: (_ for _ in ()).throw(RuntimeError("seed failure")),
        )

        original_import_module = importlib.import_module

        def fail_numpy(name: str, package: str | None = None):
            if name == "numpy.random":
                raise RuntimeError("numpy missing")
            return original_import_module(name, package)

        patcher.setattr(importlib, "import_module", fail_numpy)
        patcher.setattr(
            rl,
            "_import_apply_dialectical_reasoning",
            lambda: lambda *_args, **_kwargs: {"status": "completed"},
        )

        results = rl.reasoning_loop(
            wsde_team=NullWSDETeam(),
            task={"problem": "seed-failure"},
            critic_agent=None,
            deterministic_seed=7,
        )

        assert results == [{"status": "completed"}]

    # Deterministic seeding success covers numpy import path.
    with monkeypatch.context() as patcher:
        seed_calls: list[int] = []
        patcher.setattr(random, "seed", lambda value: seed_calls.append(value))

        class FakeNumpy:
            def __init__(self) -> None:
                self.calls: list[int] = []

            def seed(self, value: int) -> None:
                self.calls.append(value)

        numpy_random = FakeNumpy()

        def import_numpy(name: str, package: str | None = None):
            if name == "numpy.random":
                return numpy_random
            return importlib.import_module(name, package)

        patcher.setattr(importlib, "import_module", import_numpy)
        patcher.setattr(
            rl,
            "_import_apply_dialectical_reasoning",
            lambda: lambda *_args, **_kwargs: {"status": "completed"},
        )

        rl.reasoning_loop(
            wsde_team=NullWSDETeam(),
            task={"problem": "seed-success"},
            critic_agent=None,
            deterministic_seed=13,
        )

        assert seed_calls == [13]
        assert numpy_random.calls == [13]

    # Total time budget guard short-circuits the loop.
    with monkeypatch.context() as patcher:
        monotonic_values = iter([0.0, 0.2])
        patcher.setattr(rl.time, "monotonic", lambda: next(monotonic_values))
        patcher.setattr(
            rl,
            "_import_apply_dialectical_reasoning",
            lambda: lambda *_args, **_kwargs: {"status": "completed"},
        )

        assert (
            rl.reasoning_loop(
                wsde_team=NullWSDETeam(),
                task={"problem": "budget"},
                critic_agent=None,
                max_total_seconds=0.1,
            )
            == []
        )

    # Retry loop covers both retry and exhaustion branches.
    with monkeypatch.context() as patcher:
        attempt_order: list[str] = []

        def sequential(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            attempt_order.append("call")
            if len(attempt_order) == 1:
                raise RuntimeError("transient one")
            if len(attempt_order) == 2:
                raise RuntimeError("transient two")
            return {"status": "completed"}

        sleep_calls: list[float] = []
        patcher.setattr(rl.time, "sleep", lambda duration: sleep_calls.append(duration))
        patcher.setattr(rl, "_import_apply_dialectical_reasoning", lambda: sequential)

        results = rl.reasoning_loop(
            wsde_team=NullWSDETeam(),
            task={"problem": "retry"},
            critic_agent=None,
            retry_attempts=1,
            retry_backoff=0.05,
        )

        assert results == []
        assert sleep_calls == [0.05]
        assert len(attempt_order) == 2

    # Retry loop clamps sleep when respecting a total time budget.
    with monkeypatch.context() as patcher:
        attempt_counter = {"value": 0}

        def limited_retry(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            attempt_counter["value"] += 1
            if attempt_counter["value"] == 1:
                raise RuntimeError("budgeted")
            return {"status": "completed"}

        monotonic_values = iter([0.0, 0.02, 0.03, 0.03])

        def fake_monotonic() -> float:
            return next(monotonic_values)

        sleep_budget: list[float] = []
        patcher.setattr(rl.time, "monotonic", fake_monotonic)
        patcher.setattr(
            rl.time, "sleep", lambda duration: sleep_budget.append(duration)
        )
        patcher.setattr(
            rl, "_import_apply_dialectical_reasoning", lambda: limited_retry
        )

        results = rl.reasoning_loop(
            wsde_team=NullWSDETeam(),
            task={"problem": "budgeted-retry"},
            critic_agent=None,
            retry_attempts=1,
            retry_backoff=0.2,
            max_total_seconds=0.05,
        )

        assert results == [{"status": "completed"}]
        assert sleep_budget == [pytest.approx(0.02, rel=1e-9)]

    # Retry loop stops when the remaining budget is exhausted.
    with monkeypatch.context() as patcher:
        monotonic_values = iter([0.0, 0.01, 0.2, 0.2])

        def fail_forever(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            raise RuntimeError("deadline")

        patcher.setattr(rl.time, "monotonic", lambda: next(monotonic_values))
        patcher.setattr(rl.time, "sleep", lambda _duration: None)
        patcher.setattr(rl, "_import_apply_dialectical_reasoning", lambda: fail_forever)

        assert (
            rl.reasoning_loop(
                wsde_team=NullWSDETeam(),
                task={"problem": "deadline"},
                critic_agent=None,
                retry_attempts=1,
                retry_backoff=0.05,
                max_total_seconds=0.05,
            )
            == []
        )

    # None results stop the loop without appending.
    with monkeypatch.context() as patcher:
        patcher.setattr(
            rl,
            "_import_apply_dialectical_reasoning",
            lambda: lambda *_args, **_kwargs: None,
        )

        assert (
            rl.reasoning_loop(
                wsde_team=NullWSDETeam(),
                task={"problem": "void"},
                critic_agent=None,
                max_iterations=2,
            )
            == []
        )

    # DialecticalSequence payload with invalid phase triggers coordinator fallback.
    with monkeypatch.context() as patcher:
        coordinator = CoordinatorRecorder()

        class TaskStub:
            def __init__(self) -> None:
                self.syntheses: list[dict[str, Any]] = []

            def with_solution(self, synthesis: dict[str, Any]) -> "TaskStub":
                self.syntheses.append(synthesis)
                return self

        task_stub = TaskStub()

        sequence = DialecticalSequence.from_dict(
            {
                "sequence_id": "seq-branch",
                "status": "in_progress",
                "steps": [
                    {
                        "id": "step-1",
                        "timestamp": "2024-01-01T00:00:00Z",
                        "task_id": "task-1",
                        "thesis": {"content": "t"},
                        "antithesis": {
                            "id": "ant-1",
                            "timestamp": "2024-01-01T00:00:01Z",
                            "agent": "critic",
                            "critiques": [],
                            "critique_details": [],
                            "alternative_approaches": [],
                            "improvement_suggestions": [],
                        },
                        "synthesis": {"content": "s"},
                        "method": "dialectical_reasoning",
                    }
                ],
            }
        )
        sequence._payload["phase"] = "unknown"
        sequence._payload["next_phase"] = object()
        sequence._payload["synthesis"] = {"content": "s"}

        patcher.setattr(rl, "ensure_dialectical_task", lambda _task: task_stub)
        patcher.setattr(
            rl,
            "_import_apply_dialectical_reasoning",
            lambda: lambda *_args, **_kwargs: sequence,
        )

        results = rl.reasoning_loop(
            wsde_team=NullWSDETeam(),
            task={"problem": "sequence"},
            critic_agent=None,
            coordinator=coordinator,
            phase=rl.Phase.REFINE,
            max_iterations=1,
        )

        assert results == [sequence]
        assert coordinator.records and coordinator.records[0][0] == "refine"
        assert task_stub.syntheses == [{"content": "s"}]

    # Mapping payload promotes reported next_phase transitions.
    with monkeypatch.context() as patcher:
        tracker: list[str] = []

        def sequenced(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            if not tracker:
                tracker.append("first")
                return {
                    "status": "in_progress",
                    "phase": "expand",
                    "next_phase": "differentiate",
                    "synthesis": None,
                }
            tracker.append("second")
            return {"status": "completed", "phase": "differentiate"}

        patcher.setattr(rl, "_import_apply_dialectical_reasoning", lambda: sequenced)

        results = rl.reasoning_loop(
            wsde_team=NullWSDETeam(),
            task={"problem": "next-phase"},
            critic_agent=None,
            phase=rl.Phase.EXPAND,
            max_iterations=3,
        )

        assert len(results) == 2
        assert tracker == ["first", "second"]

    # Non-string next_phase values fall back to deterministic transitions.
    with monkeypatch.context() as patcher:
        sequence_map = {
            "status": "in_progress",
            "phase": "differentiate",
            "next_phase": 123,
        }

        call_counter = {"value": 0}

        def mapping_payload(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            call_counter["value"] += 1
            if call_counter["value"] == 1:
                return sequence_map
            return {"status": "completed", "phase": "refine"}

        patcher.setattr(
            rl, "_import_apply_dialectical_reasoning", lambda: mapping_payload
        )

        results = rl.reasoning_loop(
            wsde_team=NullWSDETeam(),
            task={"problem": "fallback-next"},
            critic_agent=None,
            phase=rl.Phase.DIFFERENTIATE,
            max_iterations=3,
        )

        assert len(results) == 2
        assert call_counter["value"] == 2

    # Invalid next_phase strings rely on the deterministic fallback map.
    with monkeypatch.context() as patcher:
        call_steps: list[str] = []

        def invalid_next_phase(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            call_steps.append("call")
            if len(call_steps) == 1:
                return {
                    "status": "in_progress",
                    "phase": "refine",
                    "next_phase": "???",
                }
            return {"status": "completed", "phase": "refine"}

        patcher.setattr(
            rl, "_import_apply_dialectical_reasoning", lambda: invalid_next_phase
        )

        results = rl.reasoning_loop(
            wsde_team=NullWSDETeam(),
            task={"problem": "invalid-next"},
            critic_agent=None,
            phase=rl.Phase.REFINE,
            max_iterations=2,
        )

        assert len(results) == 2
        assert call_steps == ["call", "call"]

    # Non-mapping payload raises the TypeError guard.
    with monkeypatch.context() as patcher:
        patcher.setattr(
            rl,
            "_import_apply_dialectical_reasoning",
            lambda: lambda *_args, **_kwargs: 123,
        )

        with pytest.raises(TypeError):
            rl.reasoning_loop(
                wsde_team=NullWSDETeam(),
                task={"problem": "type"},
                critic_agent=None,
            )
