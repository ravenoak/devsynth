"""Deterministic tests for the long running progress indicator."""

import importlib
import importlib.util
import itertools
import sys
import time
import types
from pathlib import Path
from typing import Dict, List

import pytest


def _install_rich_stubs() -> None:
    if "rich" in sys.modules:
        return

    rich_module = types.ModuleType("rich")
    sys.modules["rich"] = rich_module

    class _Stub:
        def __init__(self, *args, **kwargs) -> None:  # pragma: no cover - simple stub
            pass

    class Console:  # pragma: no cover - simple stub
        def __init__(self, *args, **kwargs) -> None:
            pass

        def print(self, *args, **kwargs) -> None:
            pass

    console_module = types.ModuleType("rich.console")
    console_module.Console = Console
    sys.modules["rich.console"] = console_module

    live_module = types.ModuleType("rich.live")
    live_module.Live = _Stub
    sys.modules["rich.live"] = live_module

    markdown_module = types.ModuleType("rich.markdown")
    markdown_module.Markdown = _Stub
    sys.modules["rich.markdown"] = markdown_module

    panel_module = types.ModuleType("rich.panel")
    panel_module.Panel = _Stub
    sys.modules["rich.panel"] = panel_module

    progress_module = types.ModuleType("rich.progress")
    progress_module.Progress = _Stub
    progress_module.BarColumn = _Stub
    progress_module.MofNCompleteColumn = _Stub
    progress_module.SpinnerColumn = _Stub
    progress_module.TaskProgressColumn = _Stub
    progress_module.TextColumn = _Stub
    progress_module.TimeRemainingColumn = _Stub
    progress_module.TimeElapsedColumn = _Stub
    sys.modules["rich.progress"] = progress_module

    table_module = types.ModuleType("rich.table")
    table_module.Table = _Stub
    sys.modules["rich.table"] = table_module

    text_module = types.ModuleType("rich.text")
    text_module.Text = _Stub
    sys.modules["rich.text"] = text_module

    prompt_module = types.ModuleType("rich.prompt")
    prompt_module.Confirm = _Stub
    prompt_module.Prompt = _Stub
    sys.modules["rich.prompt"] = prompt_module

    style_module = types.ModuleType("rich.style")
    style_module.Style = _Stub
    sys.modules["rich.style"] = style_module

    theme_module = types.ModuleType("rich.theme")
    theme_module.Theme = _Stub
    sys.modules["rich.theme"] = theme_module


_install_rich_stubs()


def _install_interface_stubs() -> None:
    interface_pkg_name = "devsynth.interface"
    if interface_pkg_name not in sys.modules:
        interface_pkg = types.ModuleType(interface_pkg_name)
        interface_pkg.__path__ = []  # type: ignore[attr-defined]
        sys.modules[interface_pkg_name] = interface_pkg

    ux_bridge_name = f"{interface_pkg_name}.ux_bridge"
    if ux_bridge_name not in sys.modules:
        ux_bridge_module = types.ModuleType(ux_bridge_name)

        class ProgressIndicator:  # pragma: no cover - simple stub
            def update(self, *args, **kwargs) -> None:
                pass

            def complete(self) -> None:
                pass

            def get_summary(self) -> Dict[str, object]:  # type: ignore[override]
                return {}

        class UXBridge:  # pragma: no cover - simple stub
            def __init__(self) -> None:
                self.console = None

        ux_bridge_module.ProgressIndicator = ProgressIndicator
        ux_bridge_module.UXBridge = UXBridge
        sys.modules[ux_bridge_name] = ux_bridge_module

    cli_module_name = f"{interface_pkg_name}.cli"
    if cli_module_name not in sys.modules:
        cli_module = types.ModuleType(cli_module_name)

        class CLIProgressIndicator:  # pragma: no cover - simple stub
            def __init__(self, *args, **kwargs) -> None:
                pass

        cli_module.CLIProgressIndicator = CLIProgressIndicator
        sys.modules[cli_module_name] = cli_module


_install_interface_stubs()

REPO_ROOT = Path(__file__).resolve().parents[4]
APPLICATION_DIR = REPO_ROOT / "src" / "devsynth" / "application"
CLI_DIR = APPLICATION_DIR / "cli"

import devsynth  # noqa: E402  # Ensure base package is available

if "devsynth.application" not in sys.modules:
    application_pkg = types.ModuleType("devsynth.application")
    application_pkg.__path__ = [str(APPLICATION_DIR)]  # type: ignore[attr-defined]
    sys.modules["devsynth.application"] = application_pkg

if "devsynth.application.cli" not in sys.modules:
    cli_pkg = types.ModuleType("devsynth.application.cli")
    cli_pkg.__path__ = [str(CLI_DIR)]  # type: ignore[attr-defined]
    sys.modules["devsynth.application.cli"] = cli_pkg

if "devsynth.config" not in sys.modules:
    config_module = types.ModuleType("devsynth.config")
    sys.modules["devsynth.config"] = config_module

    settings_module = types.ModuleType("devsynth.config.settings")

    def ensure_path_exists(path: Path) -> Path:  # pragma: no cover - stub
        return path

    settings_module.ensure_path_exists = ensure_path_exists
    sys.modules["devsynth.config.settings"] = settings_module
    config_module.settings = settings_module

progress_module = importlib.import_module("devsynth.application.cli.progress")

if not hasattr(progress_module, "EnhancedProgressIndicator"):

    class EnhancedProgressIndicator:  # pragma: no cover - shim for optional dependency
        def __init__(self, *args, **kwargs) -> None:
            pass

    progress_module.EnhancedProgressIndicator = EnhancedProgressIndicator
    all_names = getattr(progress_module, "__all__", [])
    if "EnhancedProgressIndicator" not in all_names:
        progress_module.__all__ = list(all_names) + ["EnhancedProgressIndicator"]

MODULE_NAME = "devsynth.application.cli.long_running_progress"
if MODULE_NAME in sys.modules:
    long_running_progress = sys.modules[MODULE_NAME]
else:
    spec = importlib.util.spec_from_file_location(
        MODULE_NAME, CLI_DIR / "long_running_progress.py"
    )
    assert spec and spec.loader  # pragma: no cover - import guard
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    long_running_progress = module

from .test_long_running_progress import DummyConsole, FakeProgress, FakeTask


@pytest.mark.fast
def test_progress_indicator_base_alias_stays_exported() -> None:
    """Ensure the module still exposes the base alias under stub imports."""

    assert hasattr(long_running_progress, "_ProgressIndicatorBase")
    base = long_running_progress._ProgressIndicatorBase
    assert base is long_running_progress.ProgressIndicator
    assert issubclass(long_running_progress.LongRunningProgressIndicator, base)


@pytest.mark.fast
def test_progress_indicator_base_alias_direct_import_succeeds() -> None:
    """Importing the alias via ``from module import`` succeeds under stubs."""

    from devsynth.application.cli.long_running_progress import (
        _ProgressIndicatorBase as imported_base,
    )

    assert imported_base is long_running_progress.ProgressIndicator
    assert issubclass(long_running_progress.LongRunningProgressIndicator, imported_base)


class CountingClock:
    """Generator-backed clock based on ``itertools.count``."""

    def __init__(self, start: float = 0.0, step: float = 1.0) -> None:
        self._iterator = itertools.count(start=start, step=step)
        self.history: List[float] = []

    def __call__(self) -> float:
        value = float(next(self._iterator))
        self.history.append(value)
        return value

    def advance(self, ticks: int) -> None:
        """Advance the clock by consuming ``ticks`` values."""

        for _ in range(ticks):
            self()


@pytest.fixture
def deterministic_clock(monkeypatch: pytest.MonkeyPatch) -> CountingClock:
    clock = CountingClock()

    def fake_time() -> float:
        return clock()

    monkeypatch.setattr(time, "time", fake_time)
    monkeypatch.setattr(long_running_progress.time, "time", fake_time)
    return clock


@pytest.fixture(autouse=True)
def fake_progress(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(long_running_progress, "Progress", FakeProgress)


def _expected_eta(
    start_time: float, current_time: float, progress_fraction: float
) -> float:
    elapsed = current_time - start_time
    return start_time + elapsed / progress_fraction


@pytest.mark.fast
def test_update_thresholds_with_deterministic_clock(
    deterministic_clock: CountingClock,
) -> None:
    console = DummyConsole()
    indicator = long_running_progress.LongRunningProgressIndicator(
        console, "main", total=100
    )

    task = indicator._progress.tasks[indicator._task]

    indicator.update(advance=2, status="Booting")
    first_update_time = deterministic_clock.history[-1]
    history = task.fields["history"]
    assert len(history) == 1
    assert history[0]["status"] == "Booting"
    assert history[0]["completed"] == pytest.approx(0)
    assert history[0]["time"] == pytest.approx(first_update_time)

    summary_before_eta = indicator.get_summary()
    assert "eta" not in summary_before_eta
    assert summary_before_eta["progress"] == pytest.approx(0.02)

    deterministic_clock.advance(4)
    indicator.update(advance=4, status="Running")
    second_update_time = deterministic_clock.history[-1]

    history = task.fields["history"]
    assert len(history) == 2
    assert history[-1]["status"] == "Running"
    assert history[-1]["completed"] == pytest.approx(2)
    assert history[-1]["time"] == pytest.approx(second_update_time)

    checkpoints = task.fields["checkpoints"]
    assert len(checkpoints) == 1
    assert checkpoints[0]["time"] == pytest.approx(second_update_time)
    assert checkpoints[0]["progress"] == pytest.approx(task.completed / task.total)
    expected_eta_checkpoint = _expected_eta(
        indicator._start_time,
        second_update_time,
        task.completed / task.total,
    )
    assert checkpoints[0]["eta"] == pytest.approx(expected_eta_checkpoint)

    summary_after_eta = indicator.get_summary()
    summary_time = deterministic_clock.history[-1]
    assert summary_after_eta["eta"] == pytest.approx(
        _expected_eta(
            indicator._start_time,
            summary_time,
            summary_after_eta["progress"],
        )
    )
    assert summary_after_eta["checkpoints"] == checkpoints

    deterministic_clock.advance(2)
    indicator.update(advance=10)
    third_update_time = deterministic_clock.history[-1]

    checkpoints = task.fields["checkpoints"]
    assert len(checkpoints) == 2
    assert [cp["progress"] for cp in checkpoints] == pytest.approx([0.06, 0.16])
    assert checkpoints[-1]["time"] == pytest.approx(third_update_time)

    summary_after_checkpoint = indicator.get_summary()
    summary_time = deterministic_clock.history[-1]
    assert summary_after_checkpoint["eta"] == pytest.approx(
        _expected_eta(
            indicator._start_time,
            summary_time,
            summary_after_checkpoint["progress"],
        )
    )
    assert summary_after_checkpoint["checkpoints"] == checkpoints


@pytest.mark.fast
def test_subtask_flow_preserves_mappings_and_progress(
    deterministic_clock: CountingClock,
) -> None:
    console = DummyConsole()
    indicator = long_running_progress.LongRunningProgressIndicator(
        console, "pipeline", total=100
    )

    main_task = indicator._progress.tasks[indicator._task]

    phase_one = indicator.add_subtask("phase 1", total=40)
    phase_two = indicator.add_subtask("phase 2", total=60)

    indicator.update_subtask(phase_one, advance=20, status="Halfway")
    first_checkpoint_time = deterministic_clock.history[-1]

    assert main_task.completed == pytest.approx(25)

    phase_one_task_id = indicator._subtasks[phase_one]
    phase_one_task = indicator._progress.tasks[phase_one_task_id]
    assert phase_one_task.completed == pytest.approx(20)
    assert phase_one_task.fields["status"] == "Halfway"

    indicator.update_subtask(phase_one, advance=0, description="phase 1b")
    assert phase_one not in indicator._subtasks
    assert "phase 1b" in indicator._subtasks
    renamed_id = indicator._subtasks["phase 1b"]
    renamed_task = indicator._progress.tasks[renamed_id]
    assert renamed_task.description.endswith("phase 1b")
    assert renamed_task.completed == pytest.approx(20)

    indicator.complete_subtask("phase 1b")
    completion_update_time = deterministic_clock.history[-1]

    assert main_task.completed == pytest.approx(50)
    assert renamed_task.completed == pytest.approx(renamed_task.total)

    summary = indicator.get_summary()
    summary_time = deterministic_clock.history[-1]

    assert summary["progress"] == pytest.approx(main_task.completed / main_task.total)
    assert summary["subtasks"] == len(indicator._subtasks)
    assert summary["checkpoints"] == main_task.fields["checkpoints"]
    assert summary["checkpoints"][0]["time"] == pytest.approx(first_checkpoint_time)
    assert summary["checkpoints"][-1]["time"] == pytest.approx(completion_update_time)
    assert summary["eta"] == pytest.approx(
        _expected_eta(
            indicator._start_time,
            summary_time,
            summary["progress"],
        )
    )

    child_tasks: Dict[int, FakeTask] = indicator._progress.child_tasks(indicator._task)
    assert set(child_tasks.keys()) == {renamed_id, indicator._subtasks[phase_two]}


@pytest.mark.fast
def test_run_with_progress_completes_after_exception(
    deterministic_clock: CountingClock, monkeypatch: pytest.MonkeyPatch
) -> None:
    console = DummyConsole()

    class DummyBridge:
        def __init__(self, console: DummyConsole) -> None:
            self.console = console

    bridge = DummyBridge(console)

    captured: Dict[str, long_running_progress.LongRunningProgressIndicator] = {}
    original_create = long_running_progress.create_long_running_progress

    def capturing_create(*args, **kwargs):
        indicator = original_create(*args, **kwargs)
        captured["indicator"] = indicator
        return indicator

    monkeypatch.setattr(
        long_running_progress,
        "create_long_running_progress",
        capturing_create,
    )

    def failing_task(progress_callback):
        progress_callback(advance=5, status="Main start")
        progress_callback(advance=10, subtask="sync", status="Syncing")
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        long_running_progress.run_with_long_running_progress(
            "main",
            failing_task,
            bridge,
            total=50,
            subtasks=[{"name": "sync", "total": 20}],
        )

    indicator = captured["indicator"]
    progress = indicator._progress
    main_task = progress.tasks[indicator._task]

    assert progress.stopped
    assert main_task.completed == pytest.approx(100)
    assert main_task.fields["status"] == "Complete"

    history_statuses = [entry["status"] for entry in main_task.fields["history"]]
    assert "Main start" in history_statuses

    checkpoints = main_task.fields["checkpoints"]
    assert len(checkpoints) >= 2
    assert checkpoints[0]["progress"] == pytest.approx(0.1)
    assert checkpoints[1]["progress"] == pytest.approx(0.6)

    subtask_id = indicator._subtasks["sync"]
    subtask_task = progress.tasks[subtask_id]
    assert subtask_task.completed == pytest.approx(subtask_task.total)
    assert subtask_task.fields["status"] == "Complete"

    assert console.messages
    last_message = console.messages[-1][0][0]
    assert last_message.startswith("[bold green]Task completed in ")
