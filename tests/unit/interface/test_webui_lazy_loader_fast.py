"""Focused fast tests for the WebUI lazy loader and router wiring."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import count
from types import SimpleNamespace

import pytest

from devsynth.interface import webui

pytestmark = pytest.mark.fast


@dataclass
class DummyProgressBar:
    """Record progress values supplied by ``st.progress``."""

    values: list[float]

    def progress(self, value: float) -> None:
        self.values.append(value)


@dataclass
class DummyContainer:
    """Capture markdown/info/empty calls issued during updates."""

    markdown_calls: list[str]
    info_calls: list[str]
    empty_calls: int = 0
    success_calls: list[str] = field(default_factory=list)
    progress_bars: list[DummyProgressBar] = field(default_factory=list)

    def markdown(self, text: str) -> None:
        self.markdown_calls.append(text)

    def info(self, text: str) -> None:
        self.info_calls.append(text)

    def empty(self) -> None:
        self.empty_calls += 1

    def success(
        self, text: str
    ) -> None:  # pragma: no cover - exercised by ``complete``
        self.success_calls.append(text)

    def progress(self, value: float) -> DummyProgressBar:
        bar = DummyProgressBar(values=[value])
        self.progress_bars.append(bar)
        return bar


class DummyStreamlit:
    """Purpose-built Streamlit replacement for progress lifecycle checks."""

    def __init__(self) -> None:
        self.empty_containers: list[DummyContainer] = []
        self.progress_bars: list[DummyProgressBar] = []
        self.success_messages: list[str] = []
        self.containers: list[DummyContainer] = []

    def empty(self) -> DummyContainer:
        container = DummyContainer(markdown_calls=[], info_calls=[])
        self.empty_containers.append(container)
        return container

    def progress(self, value: float) -> DummyProgressBar:
        bar = DummyProgressBar(values=[value])
        self.progress_bars.append(bar)
        return bar

    def container(self):
        container = DummyContainer(markdown_calls=[], info_calls=[])
        self.containers.append(container)

        class _Ctx:
            def __enter__(self_inner) -> DummyContainer:  # noqa: ANN001
                return container

            def __exit__(self_inner, exc_type, exc, tb) -> None:  # noqa: ANN001
                return None

        return _Ctx()

    def success(self, message: str) -> None:
        self.success_messages.append(message)

    def write(self, message: str) -> None:  # pragma: no cover - defensive fallback
        self.success_messages.append(message)


def test_lazy_streamlit_proxy_imports_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """``st`` forwards attribute access while caching the loaded module."""

    sentinel = SimpleNamespace(marker="streamlit-sentinel")
    imports: list[str] = []

    monkeypatch.setattr(webui, "_STREAMLIT", None, raising=False)

    def fake_import(name: str) -> SimpleNamespace:
        imports.append(name)
        return sentinel

    monkeypatch.setattr(webui.importlib, "import_module", fake_import)

    loaded = webui._require_streamlit()
    assert loaded is sentinel
    assert imports == ["streamlit"]
    assert webui._require_streamlit() is sentinel
    assert webui.st.marker == "streamlit-sentinel"
    assert webui._STREAMLIT is sentinel
    assert webui.st.marker == "streamlit-sentinel"
    assert webui.WebUI().streamlit.marker == "streamlit-sentinel"


def test_ui_progress_tracks_status_and_eta(monkeypatch: pytest.MonkeyPatch) -> None:
    """Progress lifecycle updates sanitize text, surface ETA, and mark completion."""

    stub = DummyStreamlit()
    monkeypatch.setattr(webui, "st", stub, raising=False)

    time_ticks = count(start=100, step=10)
    monkeypatch.setattr(webui.time, "time", lambda: next(time_ticks))

    ui = webui.WebUI()
    indicator = ui.create_progress("<b>Deploy</b>", total=4)

    status_container, time_container = stub.empty_containers[:2]
    progress_bar = stub.progress_bars[0]

    assert indicator._description == "&lt;b&gt;Deploy&lt;/b&gt;"
    assert progress_bar.values == [0.0, 0.0]

    indicator.update()
    assert indicator._status == "Processing..."
    assert progress_bar.values[-1] == 0.25
    assert status_container.markdown_calls[-1] == "**&lt;b&gt;Deploy&lt;/b&gt;** - 25%"
    assert time_container.info_calls[-1] == "ETA: 30 seconds"

    indicator.update()
    assert indicator._status == "Halfway there..."
    assert progress_bar.values[-1] == 0.5
    assert time_container.info_calls[-1] == "ETA: 20 seconds"

    indicator.update(status="Almost <done>")
    assert indicator._status == "Almost &lt;done&gt;"
    assert progress_bar.values[-1] == 0.75
    assert time_container.info_calls[-1] == "ETA: 10 seconds"

    subtask_id = indicator.add_subtask("Subtask <one>", total=2)
    sub_container = stub.containers[0]
    sub_bar = sub_container.progress_bars[0]
    assert sub_container.markdown_calls[-1].endswith("0%")

    indicator.update_subtask(subtask_id, description="Halfway <mark>")
    assert sub_container.markdown_calls[-1] == (
        "&nbsp;&nbsp;&nbsp;&nbsp;**Halfway &lt;mark&gt;** - 50%"
    )
    assert sub_bar.values[-1] == 0.5

    indicator.complete_subtask(subtask_id)
    assert sub_bar.values[-1] == 1.0
    assert sub_container.success_calls[-1] == "Completed: Halfway &lt;mark&gt;"

    indicator.complete()
    assert indicator._status == "Complete"
    assert progress_bar.values[-1] == 1.0
    assert time_container.empty_calls >= 1
    assert stub.success_messages[-1] == "Completed: &lt;b&gt;Deploy&lt;/b&gt;"


def test_ensure_router_creates_single_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    """Router initialization defers until first access and memoizes the instance."""

    created: list[tuple[webui.WebUI, dict[str, str]]] = []

    class RecordingRouter:
        def __init__(self, owner: webui.WebUI, navigation: dict[str, str]) -> None:
            created.append((owner, navigation))
            self.owner = owner
            self.navigation = navigation

    monkeypatch.setattr(webui, "Router", RecordingRouter)

    navigation = {"Home": "render_home", "Docs": "render_docs"}
    monkeypatch.setattr(webui.WebUI, "navigation_items", lambda self: navigation)

    ui = webui.WebUI()
    first = ui._ensure_router()
    second = ui._ensure_router()

    assert first is second
    assert created == [(ui, navigation)]
