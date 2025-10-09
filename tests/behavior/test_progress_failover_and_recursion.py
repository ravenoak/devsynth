"""Behavioral coverage for CLI progress telemetry, provider failover, and recursion guards."""

from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

pytestmark = [pytest.mark.fast]

sys.modules.setdefault("jsonschema", SimpleNamespace())
sys.modules.setdefault("toml", SimpleNamespace(load=lambda *args, **kwargs: {}))
sys.modules.setdefault("yaml", SimpleNamespace(safe_load=lambda *args, **kwargs: {}))


def _noop_dataclass(cls=None, **_kwargs):
    def wrap(inner_cls):
        return inner_cls

    if cls is None:
        return wrap
    return wrap(cls)


sys.modules.setdefault("pydantic", SimpleNamespace(ValidationError=Exception))
sys.modules.setdefault(
    "pydantic.dataclasses", SimpleNamespace(dataclass=_noop_dataclass)
)


class _RichStub:
    def __init__(self, *args, **kwargs) -> None:  # noqa: D401 - trivial stub
        """No-op stub for Rich components."""


sys.modules.setdefault("rich.console", SimpleNamespace(Console=_RichStub))
sys.modules.setdefault("rich.live", SimpleNamespace(Live=_RichStub))
sys.modules.setdefault("rich.markdown", SimpleNamespace(Markdown=_RichStub))
sys.modules.setdefault("rich.panel", SimpleNamespace(Panel=_RichStub))
sys.modules.setdefault(
    "rich.progress",
    SimpleNamespace(
        BarColumn=_RichStub,
        MofNCompleteColumn=_RichStub,
        Progress=_RichStub,
        SpinnerColumn=_RichStub,
        TaskProgressColumn=_RichStub,
        TextColumn=_RichStub,
        TimeRemainingColumn=_RichStub,
    ),
)
sys.modules.setdefault("rich.table", SimpleNamespace(Table=_RichStub))
sys.modules.setdefault("rich.text", SimpleNamespace(Text=_RichStub))

from devsynth.application.cli import long_running_progress
from devsynth.application.edrr.coordinator.core import EDRRCoordinator
from devsynth.domain.models.wsde_facade import WSDETeam


class _DummyConsole:
    def __init__(self) -> None:
        self.messages: list[tuple[tuple[Any, ...], Dict[str, Any]]] = []

    def print(self, *args: Any, **kwargs: Any) -> None:
        self.messages.append((args, kwargs))


class _BadString:
    def __str__(self) -> str:
        raise RuntimeError("boom")


class _TimeMachine:
    def __init__(self) -> None:
        self.current = 0.0
        self.history: list[float] = []

    def time(self) -> float:
        value = self.current
        self.history.append(value)
        self.current += 1.0
        return value


class _FakeTask:
    def __init__(self, description: str, total: int, **fields: Any) -> None:
        self.description = description
        self.total = total
        self.completed = 0.0
        self.fields: dict[str, Any] = dict(fields)


class _FakeProgress:
    def __init__(self, *_, **__) -> None:
        self.tasks: dict[int, _FakeTask] = {}
        self._counter = 0
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def add_task(self, description: str, *, total: int = 100, **fields: Any) -> int:
        self._counter += 1
        task_id = self._counter
        self.tasks[task_id] = _FakeTask(description, total, **fields)
        return task_id

    def update(
        self,
        task_id: int,
        *,
        advance: float = 0.0,
        completed: float | None = None,
        **fields: Any,
    ) -> _FakeTask:
        task = self.tasks[task_id]
        if completed is not None:
            task.completed = completed
        else:
            task.completed += advance
        description = fields.pop("description", None)
        if description is not None:
            task.description = description
        for key, value in fields.items():
            task.fields[key] = value
        return task


class _RecordingProgress:
    def __init__(self) -> None:
        self.description = ""
        self.total = 0
        self.complete_called = False
        self.update_calls: list[dict[str, Any]] = []
        self.subtasks: dict[str, dict[str, Any]] = {}

    def add_subtask(self, name: str, **fields: Any) -> str:
        self.subtasks[name] = fields
        return name

    def update(self, **payload: Any) -> None:
        self.update_calls.append(payload)

    def update_subtask(self, name: str, *args: Any, **kwargs: Any) -> None:
        self.subtasks.setdefault(name, {}).update({"args": args, "kwargs": kwargs})

    def complete(self) -> None:
        self.complete_called = True


@pytest.mark.requires_resource("cli")
def test_long_running_progress_records_telemetry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Feature: long_running_progress.feature Scenario: Telemetry for CLI tasks."""

    clock = _TimeMachine()
    monkeypatch.setattr(long_running_progress.time, "time", clock.time)
    monkeypatch.setattr(long_running_progress, "time", SimpleNamespace(time=clock.time))
    monkeypatch.setattr(long_running_progress, "Progress", _FakeProgress)

    console = _DummyConsole()
    indicator = long_running_progress.LongRunningProgressIndicator(console, "etl", 100)

    indicator.update(status="warming up")
    indicator.update(advance=10, status="processing")
    indicator.update(advance=15, description=_BadString())

    subtask = indicator.add_subtask(_BadString(), total=50, status="queued")
    indicator.update_subtask(subtask, advance=10, description="phase-one")
    indicator.update(status="in flight", advance=40)
    indicator.complete()

    summary = indicator.get_summary()

    task = indicator._progress.tasks[indicator._task]
    assert task.fields["status"] == "Complete"
    assert task.fields["history"][-1]["status"] == "in flight"
    assert task.fields["checkpoints"], "Expected checkpoint telemetry to be captured"
    assert task.description == "<description>"
    assert summary["description"] == "<description>"
    assert summary["history"][-1]["status"] == "in flight"
    assert summary["checkpoints"]
    assert indicator._progress.stopped is True
    assert console.messages[-1][0][0].startswith("[bold green]Task completed in")


@pytest.mark.requires_resource("cli")
def test_run_with_long_running_progress_completes_on_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Feature: long_running_progress.feature Scenario: Progress completes on error."""

    recorder = _RecordingProgress()
    monkeypatch.setattr(
        long_running_progress,
        "create_long_running_progress",
        lambda console, description, total: recorder,
    )

    class _Bridge:
        console = object()

    def _failing_task(**kwargs: Any) -> None:
        assert "progress_callback" in kwargs
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        long_running_progress.run_with_long_running_progress(
            "demo", _failing_task, _Bridge()
        )

    assert recorder.complete_called is True


@pytest.mark.no_network
def test_provider_factory_falls_back_to_stub_offline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Feature: edrr_integration_with_real_llm_providers.feature Scenario: Offline fallback."""

    from devsynth.adapters import provider_system

    for key in [
        "OPENAI_API_KEY",
        "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE",
        "DEVSYNTH_PROVIDER",
    ]:
        monkeypatch.delenv(key, raising=False)

    monkeypatch.setenv("DEVSYNTH_OFFLINE", "1")
    monkeypatch.setenv("DEVSYNTH_SAFE_DEFAULT_PROVIDER", "stub")

    settings = SimpleNamespace(
        provider_max_retries=1,
        provider_initial_delay=0.1,
        provider_exponential_base=2.0,
        provider_max_delay=1.0,
        provider_jitter=False,
        provider_conditions=[],
        provider_track_metrics=True,
        tls_verify=True,
        tls_cert_file=None,
        tls_key_file=None,
        tls_ca_file=None,
    )
    monkeypatch.setattr(provider_system, "get_settings", lambda reload=False: settings)

    provider = provider_system.ProviderFactory.create_provider("openai")
    assert isinstance(provider, provider_system.StubProvider)
    assert provider.retry_config["max_retries"] == settings.provider_max_retries


class _MemoryManagerStub:
    def register_sync_hook(
        self, hook
    ):  # noqa: ANN001 - signature dictated by coordinator
        self.hook = hook

    def retrieve_historical_patterns(self):  # noqa: D401
        """Return no historical recursion overrides."""
        return []


@pytest.mark.integration
def test_recursion_termination_at_max_depth(monkeypatch: pytest.MonkeyPatch) -> None:
    """Feature: edrr_recursion_termination.feature Scenario: Max-depth guard wins."""

    coordinator = EDRRCoordinator(
        memory_manager=_MemoryManagerStub(),
        wsde_team=MagicMock(spec=WSDETeam),
        code_analyzer=MagicMock(),
        ast_transformer=MagicMock(),
        prompt_manager=MagicMock(),
        documentation_manager=MagicMock(),
    )

    coordinator.recursion_depth = coordinator.max_recursion_depth
    should_stop, reason = coordinator.should_terminate_recursion({})

    assert should_stop is True
    assert "max_depth" in (reason or "")

    override_stop, override_reason = coordinator.should_terminate_recursion(
        {"human_override": "continue"}
    )
    assert override_stop is False
    assert override_reason is None
