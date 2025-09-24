"""Progress summary rendering for the gather wizard."""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import MagicMock

import pytest

import devsynth.interface.webui.rendering as rendering
from devsynth.interface.webui.rendering import ProjectSetupPages
from tests.unit.interface.test_webui_behavior_checklist_fast import (
    BehaviorStreamlitStub,
    ContainerRecorder,
)


class _Harness(ProjectSetupPages):
    """Project setup harness that records rendered messages."""

    def __init__(self, st: BehaviorStreamlitStub) -> None:
        self.streamlit = st
        self.messages: list[str] = []

    def display_result(self, message: str, **_kwargs: Any) -> None:
        self.messages.append(message)


class _FakeWizardState:
    def __init__(self, current_step: int, total_steps: int) -> None:
        self._current_step = current_step
        self._total_steps = total_steps

    def get_current_step(self) -> int:
        return self._current_step

    def get_total_steps(self) -> int:
        return self._total_steps


class _FakeWizardManager:
    def __init__(self) -> None:
        self._state = _FakeWizardState(3, 3)
        self.values: dict[str, Any] = {"wizard_started": True}
        self.reset_calls = 0
        self.cleared: list[tuple[str, ...]] = []
        self.completed = False

    def get_wizard_state(self) -> _FakeWizardState:
        return self._state

    def reset_wizard_state(self) -> bool:
        self.reset_calls += 1
        return True

    def clear_temporary_state(self, keys: list[str]) -> bool:
        self.cleared.append(tuple(keys))
        return True

    def set_value(self, key: str, value: Any) -> None:
        self.values[key] = value

    def get_value(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def set_completed(self, completed: bool = True) -> bool:
        self.completed = completed
        return True

    def next_step(self) -> bool:
        self._state._current_step = min(  # noqa: SLF001 - test stub
            self._state._total_steps,  # noqa: SLF001 - test stub
            self._state._current_step + 1,
        )
        return True

    def previous_step(self) -> bool:
        self._state._current_step = max(1, self._state._current_step - 1)
        return True


def _noop(
    self: ProjectSetupPages, wizard_state: Any
) -> None:  # noqa: ANN001 - test helper
    return None


def _always_valid(
    self: ProjectSetupPages, wizard_state: Any, step: int
) -> bool:  # noqa: ANN001 - test helper
    return True


@pytest.mark.fast
def test_gather_wizard_renders_cli_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    """The gather wizard mirrors CLI progress summaries with sanitized output."""

    frozen_now = 1_700_000_015.0
    monkeypatch.setattr(rendering.time, "time", lambda: frozen_now)
    monkeypatch.setattr(time, "time", lambda: frozen_now)

    stub = BehaviorStreamlitStub()
    stub.button = MagicMock(side_effect=[False, False, False, True])
    stub.columns = MagicMock(
        return_value=tuple(ContainerRecorder(stub, f"column[{i}]") for i in range(3))
    )
    stub.experimental_rerun = MagicMock()

    monkeypatch.setattr(rendering.ProjectSetupPages, "_handle_gather_step_1", _noop)
    monkeypatch.setattr(rendering.ProjectSetupPages, "_handle_gather_step_2", _noop)
    monkeypatch.setattr(rendering.ProjectSetupPages, "_handle_gather_step_3", _noop)
    monkeypatch.setattr(
        rendering.ProjectSetupPages, "_validate_gather_step", _always_valid
    )

    fake_manager = _FakeWizardManager()

    def fake_create_wizard_manager(
        _session_state: Any,
        _wizard_name: str,
        *,
        steps: int,
        initial_state: dict[str, Any] | None = None,
    ) -> _FakeWizardManager:
        assert steps == 3
        assert initial_state is not None
        return fake_manager

    monkeypatch.setattr(
        rendering.WebUIBridge,
        "create_wizard_manager",
        fake_create_wizard_manager,
    )

    eta_ts = frozen_now + 90.0
    fake_summary = {
        "description": "<Gather & Save>",
        "progress": 1.0,
        "elapsed": 42.0,
        "remaining_str": "0:00:00",
        "eta": eta_ts,
        "eta_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(eta_ts)),
        "history": [
            {"time": frozen_now - 10, "status": "Queued <init>", "completed": 0},
            {"time": frozen_now - 5, "status": "Collecting > sources", "completed": 50},
            {"time": frozen_now, "status": "Complete & verify", "completed": 100},
        ],
        "checkpoints": [
            {"time": frozen_now - 9, "progress": 0.25, "eta": eta_ts},
            {"time": frozen_now - 3, "progress": 0.75, "eta": eta_ts},
        ],
        "subtasks_detail": [
            {
                "description": "Docs <survey>",
                "progress": 1.0,
                "status": "Complete",
                "history": [
                    {
                        "time": frozen_now - 8,
                        "status": "Scanning & tagging",
                        "completed": 50,
                    },
                    {
                        "time": frozen_now - 6,
                        "status": "Summaries ready",
                        "completed": 100,
                    },
                ],
                "checkpoints": [
                    {"time": frozen_now - 7, "progress": 0.5, "eta": frozen_now - 2},
                ],
            },
            {
                "description": "Stakeholder interviews & analysis",
                "progress": 0.5,
                "status": "In progress",
                "history": [
                    {"time": frozen_now - 4, "status": "Scheduling", "completed": 20},
                ],
            },
        ],
    }

    gather_calls: list[ProjectSetupPages] = []

    def fake_gather(bridge: ProjectSetupPages) -> dict[str, Any]:
        gather_calls.append(bridge)
        return fake_summary

    monkeypatch.setattr(rendering, "gather_requirements", fake_gather)

    captured_run: dict[str, Any] = {}

    def fake_run_with_progress(
        task_name: str,
        task_fn,
        bridge: ProjectSetupPages,
        total: int = 100,
        subtasks: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        captured_run.update(
            {
                "task_name": task_name,
                "bridge": bridge,
                "total": total,
                "subtasks": subtasks,
            }
        )
        return task_fn()

    monkeypatch.setattr(rendering, "run_with_progress", fake_run_with_progress)

    ui = _Harness(stub)
    ui._gather_wizard()

    expected_keys = (
        "resource_type_select",
        "resource_location_input",
        "metadata_author_input",
        "metadata_version_input",
        "metadata_tags_input",
        "metadata_doc_type_select",
        "metadata_language_select",
        "metadata_custom_field_name_input",
        "metadata_custom_field_value_input",
    )

    assert captured_run["task_name"] == "Processing resources..."
    assert captured_run["bridge"] is ui
    assert captured_run["total"] == 100
    assert captured_run["subtasks"] == [
        {"name": ui._get_gather_step_title(i), "total": 100} for i in range(1, 4)
    ]
    assert gather_calls == [ui]
    assert fake_manager.completed is True
    assert fake_manager.reset_calls == 1
    assert fake_manager.cleared == [expected_keys]
    assert stub.experimental_rerun.called
    assert ui.messages[-1] == "[green]Resources gathered successfully![/green]"

    assert len(stub.progress_bars) == 4
    wizard_bar, main_bar, docs_bar, interviews_bar = stub.progress_bars
    assert wizard_bar.values == [1.0]
    assert main_bar.values == [1.0]
    assert docs_bar.values == [1.0]
    assert interviews_bar.values == [0.5]

    assert len(stub.containers) == 5
    (
        main_container,
        history_container,
        checkpoints_container,
        docs_container,
        interviews_container,
    ) = stub.containers

    expected_eta = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(eta_ts))
    expected_eta_time = time.strftime("%H:%M:%S", time.localtime(eta_ts))
    assert (
        main_container.markdown_calls[0]
        == "**&lt;Gather &amp; Save&gt;** — 100% complete"
    )
    assert (
        main_container.info_calls[0]
        == f"ETA {expected_eta} (in 90s) • Remaining 0:00:00 • Elapsed 42s"
    )

    history_times = [
        time.strftime("%H:%M:%S", time.localtime(ts))
        for ts in (frozen_now - 10, frozen_now - 5, frozen_now)
    ]
    assert history_container.markdown_calls == [
        "**History**",
        f"- 0% • Queued &lt;init&gt; • {history_times[0]}",
        f"- 50% • Collecting &gt; sources • {history_times[1]}",
        f"- 100% • Complete &amp; verify • {history_times[2]}",
    ]

    checkpoint_times = [
        time.strftime("%H:%M:%S", time.localtime(ts))
        for ts in (frozen_now - 9, frozen_now - 3)
    ]
    assert checkpoints_container.markdown_calls == ["**Checkpoints**"]
    assert checkpoints_container.info_calls == [
        f"25% • {checkpoint_times[0]} • ETA {expected_eta_time} (in 90s)",
        f"75% • {checkpoint_times[1]} • ETA {expected_eta_time} (in 90s)",
    ]

    doc_history_times = [
        time.strftime("%H:%M:%S", time.localtime(ts))
        for ts in (frozen_now - 8, frozen_now - 6)
    ]
    assert docs_container.markdown_calls == [
        "**Docs &lt;survey&gt;** — 100% complete",
        "- Status: Complete",
        f"- 50% • Scanning &amp; tagging • {doc_history_times[0]}",
        f"- 100% • Summaries ready • {doc_history_times[1]}",
    ]
    doc_checkpoint_time = time.strftime("%H:%M:%S", time.localtime(frozen_now - 7))
    doc_eta_time = time.strftime("%H:%M:%S", time.localtime(frozen_now - 2))
    assert docs_container.info_calls == [
        f"50% • {doc_checkpoint_time} • ETA {doc_eta_time} (in 0s)"
    ]

    interview_history_time = time.strftime("%H:%M:%S", time.localtime(frozen_now - 4))
    assert interviews_container.markdown_calls == [
        "**Stakeholder interviews &amp; analysis** — 50% complete",
        "- Status: In progress",
        f"- 20% • Scheduling • {interview_history_time}",
    ]
    assert interviews_container.info_calls == []

    assert stub.button.call_count == 4
