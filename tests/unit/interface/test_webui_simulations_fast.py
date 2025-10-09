"""Deterministic WebUI simulations covering progress and error sanitisation."""

from __future__ import annotations

import importlib
import itertools
from typing import Any

import pytest

import devsynth.interface.webui as webui
import devsynth.interface.webui.rendering as rendering
import devsynth.interface.webui_bridge as webui_bridge
from devsynth.interface.webui.rendering import ProjectSetupPages
from tests.unit.interface.test_webui_behavior_checklist_fast import (
    BehaviorStreamlitStub,
)


class _LinearClock:
    def __init__(self, start: float = 0.0, step: float = 1.0) -> None:
        self._values = itertools.count(start=start, step=step)
        self.history: list[float] = []

    def __call__(self) -> float:
        value = float(next(self._values))
        self.history.append(value)
        return value


class RenderHarness(ProjectSetupPages):
    def __init__(self, st: BehaviorStreamlitStub) -> None:
        self.streamlit = st
        self.error_messages: list[str] = []

    def display_result(self, message: str, **_kwargs: Any) -> None:
        self.error_messages.append(message)


class _Boom:
    def __str__(self) -> str:  # pragma: no cover - exercised via sanitisation
        raise RuntimeError("boom")


@pytest.mark.fast
def test_rendering_simulation_records_summary_and_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """simulate_progress_rendering mirrors CLI telemetry and sanitises errors."""

    stub = BehaviorStreamlitStub()
    harness = RenderHarness(stub)

    summary = {
        "description": "Gather <docs>",
        "progress": 0.75,
        "remaining": 45.0,
        "elapsed": 90.0,
        "eta": 200.0,
        "history": [
            {"status": "Queued <init>", "progress": 0.25, "time": 100.0},
            {"status": "Collecting", "progress": 0.5, "time": 150.0},
        ],
        "checkpoints": [
            {"progress": 0.25, "time": 110.0, "eta": 200.0},
            {"progress": 0.5, "time": 160.0, "eta": 200.0},
        ],
        "subtasks_detail": [
            {
                "description": "Docs <survey>",
                "progress": 1.0,
                "status": "Complete",
                "history": [
                    {"status": "Scanning", "progress": 0.5, "time": 140.0},
                ],
                "checkpoints": [
                    {"progress": 0.5, "time": 145.0, "eta": 150.0},
                ],
            }
        ],
    }

    clock = _LinearClock(start=100.0, step=5.0)
    result = rendering.simulate_progress_rendering(
        harness,
        summary,
        errors=["<boom & fail>"],
        clock=clock,
    )

    assert [event[0] for event in result["events"]] == ["summary", "error"]
    assert result["events"][1][1]["message"] == "&lt;boom &amp; fail&gt;"
    assert harness.error_messages == ["&lt;boom &amp; fail&gt;"]

    # Summary rendering populates the main progress bar and history containers.
    assert stub.progress_bars
    assert any(
        markdown.endswith("75% complete")
        for container in stub.containers
        for markdown in container.markdown_calls
    )


@pytest.mark.fast
def test_rendering_simulation_handles_nested_summary_and_clock() -> None:
    """simulate_progress_rendering formats nested history with a scripted clock."""

    stub = BehaviorStreamlitStub()
    harness = RenderHarness(stub)
    primary = stub.container()

    summary = {
        "description": "Main <summary>",
        "progress": 0.5,
        "eta": 250.0,
        "remaining": 120.0,
        "elapsed": 80.0,
        "history": [
            {"status": "Queued <1>", "progress": 0.1, "time": 50.0},
            {
                "status": "Processing",
                "completed": 30,
                "total": 100,
                "time": 70.0,
            },
        ],
        "checkpoints": [
            {"progress": 0.25, "time": 60.0, "eta": 250.0},
            {"completed": 80, "total": 100, "time": 80.0, "eta": 250.0},
        ],
        "subtasks_detail": [
            {
                "description": "stage <alpha>",
                "progress": 0.75,
                "status": "Working <soon>",
                "history": [
                    {"status": "Primed <1>", "progress": 0.25, "time": 40.0},
                    {
                        "status": "Working",
                        "completed": 30,
                        "total": 40,
                        "time": 70.0,
                    },
                ],
                "checkpoints": [
                    {"progress": 0.5, "time": 45.0, "eta": 250.0},
                ],
            },
            {
                "description": "stage beta",
                "completed": 20,
                "total": 40,
                "status": "Queued",
                "history": [
                    {
                        "status": "Queued",
                        "completed": 10,
                        "total": 40,
                        "time": 65.0,
                    }
                ],
                "checkpoints": [
                    {"completed": 20, "total": 40, "time": 75.0, "eta": 250.0},
                ],
            },
        ],
    }

    clock = _LinearClock(start=200.0, step=0.0)
    result = rendering.simulate_progress_rendering(
        harness,
        summary,
        container=primary,
        errors=["<primary>", "<secondary>"],
        clock=clock,
    )

    assert [event[0] for event in result["events"]] == [
        "summary",
        "error",
        "error",
    ]
    assert result["events"][0][1]["description"] == "Main &lt;summary&gt;"
    assert harness.error_messages == ["&lt;primary&gt;", "&lt;secondary&gt;"]
    assert result["streamlit"] is stub

    assert primary.markdown_calls[0] == "**Main &lt;summary&gt;** — 50% complete"
    assert primary.progress_bars[0].values[-1] == pytest.approx(0.5)
    assert any(
        "ETA 1970-01-01 00:04:10" in info and "Remaining 120s" in info
        for info in primary.info_calls
    )
    assert any("Elapsed 80s" in info for info in primary.info_calls)

    assert len(stub.containers) >= 5
    history_container = stub.containers[1]
    checkpoint_container = stub.containers[2]
    subtask_containers = stub.containers[3:5]

    assert history_container.markdown_calls[0] == "**History**"
    assert any("Queued &lt;1&gt;" in call for call in history_container.markdown_calls)
    assert any("00:01:10" in call for call in history_container.markdown_calls)

    assert checkpoint_container.markdown_calls[0] == "**Checkpoints**"
    assert any(
        "25%" in info and "ETA 00:04:10" in info
        for info in checkpoint_container.info_calls
    )

    assert len(subtask_containers) == 2
    assert (
        subtask_containers[0].markdown_calls[0]
        == "**stage &lt;alpha&gt;** — 75% complete"
    )
    assert any(
        "Primed &lt;1&gt;" in call for call in subtask_containers[0].markdown_calls
    )
    assert any("ETA 00:04:10" in info for info in subtask_containers[0].info_calls)
    assert subtask_containers[1].markdown_calls[0] == "**stage beta** — 50% complete"
    assert any("25%" in call for call in subtask_containers[1].markdown_calls)

    # Clock recorded the time lookups performed during rendering.
    assert len(clock.history) >= 3


@pytest.mark.fast
def test_ui_progress_simulation_drives_eta_and_completion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """WebUI._UIProgress under a stubbed Streamlit emits ETA and success messages."""

    stub = BehaviorStreamlitStub()
    monkeypatch.setattr(webui, "st", stub, raising=False)
    monkeypatch.setattr(webui, "_STREAMLIT", stub, raising=False)

    clock_values = iter([0.0, 2.0, 4.0, 6.5, 9.0, 12.0, 15.5, 18.0, 20.0])

    def fake_time() -> float:
        try:
            return float(next(clock_values))
        except StopIteration:
            return 20.0

    monkeypatch.setattr(webui.time, "time", fake_time, raising=False)

    ui = webui.WebUI()
    progress = ui.create_progress("Main <task>", total=100)
    stage_one = progress.add_subtask("Stage <1>", total=40)
    stage_two = progress.add_subtask("Stage 2", total=60)

    progress.update(advance=20)
    progress.update_subtask(stage_one, advance=20, status="Halfway")
    progress.update_subtask(stage_two, advance=30)
    progress.complete_subtask(stage_one)
    progress.update(advance=40)
    progress.complete()

    status_container, eta_container = stub.empty_containers[:2]
    assert status_container.markdown_calls[-1].startswith("**Main &lt;task&gt;**")
    assert any("ETA" in info for info in eta_container.info_calls)
    assert stub.success_calls[-1] == "Completed: Main &lt;task&gt;"

    # Subtask markdown reflects sanitised descriptions and status updates.
    assert any(
        "Stage &lt;1&gt;" in call
        for container in stub.containers
        for call in container.markdown_calls
    )


@pytest.mark.fast
def test_webui_display_result_sanitises_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """display_result escapes markup before routing to Streamlit error channel."""

    stub = BehaviorStreamlitStub()
    monkeypatch.setattr(webui, "st", stub, raising=False)
    monkeypatch.setattr(webui, "_STREAMLIT", stub, raising=False)

    ui = webui.WebUI()
    ui.display_result("ERROR build <failed>", message_type="error")

    assert stub.error_calls[-1] == "ERROR build &lt;failed&gt;"


@pytest.mark.fast
def test_webui_bridge_simulation_sanitises_nested_tasks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """WebUIProgressIndicator mirrors nested cascades with safe fallbacks."""

    clock = _LinearClock(start=0.0, step=3.0)
    monkeypatch.setattr(webui_bridge.time, "time", clock, raising=False)

    indicator = webui_bridge.WebUIProgressIndicator("Root", 100)
    child = indicator.add_subtask(_Boom(), total=40)
    nested = indicator.add_nested_subtask(child, _Boom(), total=10, status=_Boom())

    indicator.update_nested_subtask(child, nested, advance=5)
    indicator.update_subtask(child, advance=15, description=_Boom())
    indicator.complete_nested_subtask(child, nested)
    indicator.complete_subtask(child)
    indicator.complete()

    child_state = indicator._subtasks[child]
    assert child_state.description == "<subtask>"
    assert child_state.status == "Complete"

    nested_state = child_state.nested_subtasks[nested]
    assert nested_state.description == "<nested subtask>"
    assert nested_state.status == "Complete"

    assert (
        webui_bridge.WebUIBridge.adjust_wizard_step(0, direction="back", total=2) == 0
    )
    assert (
        webui_bridge.WebUIBridge.adjust_wizard_step(0, direction="next", total=2) == 1
    )
    assert webui_bridge.WebUIBridge.normalize_wizard_step(" 3.7 ", total=5) == 3
    assert webui_bridge.WebUIBridge.normalize_wizard_step("oops", total=5) == 0


@pytest.mark.fast
def test_webui_require_streamlit_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """The WebUI lazy loader imports Streamlit once and caches the module."""

    sentinel = object()
    calls: list[str] = []

    def fake_import(name: str) -> object:
        calls.append(name)
        return sentinel

    monkeypatch.setattr(webui, "_STREAMLIT", None, raising=False)
    monkeypatch.setattr(importlib, "import_module", fake_import)

    loaded = webui._require_streamlit()
    assert loaded is sentinel
    assert webui._require_streamlit() is sentinel
    assert calls == ["streamlit"]


@pytest.mark.fast
def test_webui_bridge_require_streamlit_guidance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bridge `_require_streamlit` surfaces install guidance on failure."""

    monkeypatch.setattr(webui_bridge, "st", None, raising=False)

    def fake_import(name: str) -> object:
        raise ImportError(name)

    monkeypatch.setattr(importlib, "import_module", fake_import)

    with pytest.raises(webui_bridge.DevSynthError) as excinfo:
        webui_bridge._require_streamlit()

    assert "poetry install --with dev --extras webui" in str(excinfo.value)
