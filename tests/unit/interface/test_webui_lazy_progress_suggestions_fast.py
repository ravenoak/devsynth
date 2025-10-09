"""Fast regression coverage for Streamlit lazy loading and progress rendering."""

from __future__ import annotations

import importlib
from collections.abc import Iterator
from types import SimpleNamespace

import pytest

from devsynth.exceptions import DevSynthError
from devsynth.interface import webui
from tests.helpers.dummies import DummyStreamlit

pytestmark = [pytest.mark.fast]


class _ProgressRecorder:
    """Record percentage updates written to a Streamlit progress bar."""

    def __init__(self, owner: "_HarnessStreamlit") -> None:
        self.owner = owner
        self.values: list[float] = []

    def progress(self, value: float) -> None:
        self.values.append(value)
        self.owner.progress_updates.append(value)


class _ContainerRecorder:
    """Capture markdown/info/empty/success calls routed through containers."""

    def __init__(self, owner: "_HarnessStreamlit", label: str) -> None:
        self.owner = owner
        self.label = label
        self.markdown_calls: list[tuple[str, dict]] = []
        self.info_calls: list[tuple[str, dict]] = []
        self.empty_calls = 0
        self.success_calls: list[tuple[str, dict]] = []
        self.progress_bars: list[_ProgressRecorder] = []

    def markdown(self, text: str, **kwargs) -> None:
        self.markdown_calls.append((text, kwargs))
        self.owner.markdown(text, **kwargs)

    def info(self, text: str, **kwargs) -> None:
        self.info_calls.append((text, kwargs))
        self.owner.info(text, **kwargs)

    def empty(self) -> None:
        self.empty_calls += 1

    def success(self, text: str, **kwargs) -> None:
        self.success_calls.append((text, kwargs))
        self.owner.success(text, **kwargs)

    def progress(self, value: float) -> _ProgressRecorder:
        bar = _ProgressRecorder(self.owner)
        bar.progress(value)
        self.progress_bars.append(bar)
        return bar

    def __enter__(self) -> "_ContainerRecorder":
        self.owner.container_entries.append(self.label)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None


class _HarnessStreamlit(DummyStreamlit):
    """Extend :class:`DummyStreamlit` with progress/empty helpers used by WebUI."""

    def __init__(self) -> None:
        super().__init__()
        self.import_requests = 0
        self.progress_updates: list[float] = []
        self.empty_slots: list[_ContainerRecorder] = []
        self.containers: list[_ContainerRecorder] = []
        self.container_entries: list[str] = []
        self.components = SimpleNamespace(
            v1=SimpleNamespace(html=lambda *_, **__: None)
        )

    def empty(self) -> _ContainerRecorder:
        label = f"empty[{len(self.empty_slots)}]"
        container = _ContainerRecorder(self, label)
        self.empty_slots.append(container)
        return container

    def progress(self, value: float) -> _ProgressRecorder:
        bar = _ProgressRecorder(self)
        bar.progress(value)
        return bar

    def container(self) -> _ContainerRecorder:
        label = f"container[{len(self.containers)}]"
        container = _ContainerRecorder(self, label)
        self.containers.append(container)
        return container


@pytest.fixture()
def harness_streamlit(monkeypatch: pytest.MonkeyPatch) -> Iterator[_HarnessStreamlit]:
    """Install the harness as the cached Streamlit module for the duration."""

    original_import = importlib.import_module
    stub = _HarnessStreamlit()

    def fake_import(name: str, package: str | None = None):
        if name == "streamlit":
            stub.import_requests += 1
            return stub
        return original_import(name, package)

    monkeypatch.setattr(webui, "_STREAMLIT", None)
    monkeypatch.setattr(importlib, "import_module", fake_import)
    yield stub
    monkeypatch.setattr(webui, "_STREAMLIT", None)


def test_lazy_streamlit_proxy_imports_once(
    harness_streamlit: _HarnessStreamlit,
) -> None:
    """``_LazyStreamlit`` pulls attributes from the cached module exactly once."""

    webui.st.write("hello")
    assert harness_streamlit.import_requests == 1
    webui.st.success("done")
    assert harness_streamlit.import_requests == 1
    assert harness_streamlit.writes == [(("hello",), {})]
    assert harness_streamlit.successes == ["done"]


def test_missing_streamlit_surfaces_install_guidance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Import failures raise :class:`DevSynthError` with actionable guidance."""

    monkeypatch.setattr(webui, "_STREAMLIT", None)
    original_import = importlib.import_module

    def fail_import(name: str, package: str | None = None):
        if name == "streamlit":
            raise ImportError("streamlit unavailable")
        return original_import(name, package)

    monkeypatch.setattr(importlib, "import_module", fail_import)

    with pytest.raises(DevSynthError) as excinfo:
        webui.st.write("trigger import")

    assert "poetry install --with dev --extras webui" in str(excinfo.value)


def test_progress_indicator_emits_eta_and_sanitized_status(
    harness_streamlit: _HarnessStreamlit, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Progress indicators surface ETA/status updates using sanitized content."""

    times = iter([0.0, 1.0, 2.0, 5.0, 7.0])
    monkeypatch.setattr(webui.time, "time", lambda: next(times))

    progress = webui.WebUI().create_progress("<b>Main Task</b>", total=100)

    status_container = harness_streamlit.empty_slots[0]
    assert (
        status_container.markdown_calls[0][0] == "**&lt;b&gt;Main Task&lt;/b&gt;** - 0%"
    )

    progress.update(advance=40, description="<i>Phase</i>")
    assert (
        status_container.markdown_calls[-1][0] == "**&lt;i&gt;Phase&lt;/i&gt;** - 40%"
    )

    time_container = harness_streamlit.empty_slots[1]
    assert any(call[0].startswith("ETA:") for call in time_container.info_calls)
    assert all("<" not in call[0] for call in time_container.info_calls)

    progress.update(advance=40)
    assert len(time_container.info_calls) >= 2

    subtask_id = progress.add_subtask("<tag>Subtask</tag>", total=20)
    sub_container = harness_streamlit.containers[0]
    assert sub_container.markdown_calls[0][0].startswith(
        "&nbsp;&nbsp;&nbsp;&nbsp;**&lt;tag&gt;Subtask&lt;/tag&gt;** - 0%"
    )

    progress.update_subtask(subtask_id, advance=10, status="<u>half</u>")
    assert any(
        "&lt;u&gt;half&lt;/u&gt;" in call[0] for call in sub_container.markdown_calls
    )

    progress.complete()
    assert harness_streamlit.progress_updates[-1] == 1.0
    assert harness_streamlit.successes[-1] == "Completed: &lt;i&gt;Phase&lt;/i&gt;"
    assert time_container.empty_calls >= 1


def test_permission_denied_error_renders_suggestions(
    harness_streamlit: _HarnessStreamlit,
) -> None:
    """Permission errors emit sanitized banner, suggestions, and documentation."""

    ui = webui.WebUI()
    ui.display_result("ERROR: Permission denied for <config>")

    assert harness_streamlit.errors == ["ERROR: Permission denied for &lt;config&gt;"]
    markdown_texts = [text for text, _ in harness_streamlit.markdown_calls]
    assert "**Suggestions:**" in markdown_texts
    assert any(
        "Check that you have the necessary permissions" in text
        for text in markdown_texts
    )
    assert any("[Permission Issues]" in text for text in markdown_texts)
