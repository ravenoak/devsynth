"""Unit tests exercising WebUI behavior with a synthetic Streamlit stub."""

from __future__ import annotations

import importlib
from types import SimpleNamespace
from typing import Any, Callable

import pytest

from devsynth.exceptions import DevSynthError
from devsynth.interface import webui

pytestmark = [pytest.mark.fast]


class SessionState(dict):
    """Dictionary-backed session state providing attribute-style access."""

    def __getattr__(self, name: str) -> Any:
        if name in self:
            return self[name]
        raise AttributeError(name)

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


class ProgressBarStub:
    """Capture values written to a Streamlit progress bar."""

    def __init__(self, owner: "StreamlitStub", label: str) -> None:
        self.owner = owner
        self.label = label
        self.values: list[float] = []

    def progress(self, value: float) -> None:
        self.values.append(value)
        self.owner.calls.append((f"{self.label}.progress", (value,), {}))


class ContainerStub:
    """Track markdown/info/success calls routed through containers."""

    def __init__(self, owner: "StreamlitStub", label: str) -> None:
        self.owner = owner
        self.label = label
        self.records: list[tuple[str, Any, dict[str, Any]]] = []

    def markdown(self, text: str, **kwargs: Any) -> None:
        self.records.append(("markdown", text, kwargs))
        self.owner.calls.append((f"{self.label}.markdown", (text,), kwargs))

    def info(self, text: str, **kwargs: Any) -> None:
        self.records.append(("info", text, kwargs))
        self.owner.calls.append((f"{self.label}.info", (text,), kwargs))

    def empty(self) -> None:
        self.records.append(("empty", None, {}))
        self.owner.calls.append((f"{self.label}.empty", (), {}))

    def success(self, text: str, **kwargs: Any) -> None:
        self.records.append(("success", text, kwargs))
        self.owner.calls.append((f"{self.label}.success", (text,), kwargs))

    def progress(self, value: float) -> ProgressBarStub:
        bar = ProgressBarStub(self.owner, f"{self.label}.progress")
        self.records.append(("progress", value, {}))
        self.owner.calls.append((f"{self.label}.progress", (value,), {}))
        self.owner.progress_bars.append(bar)
        return bar

    def __enter__(self) -> "ContainerStub":
        self.owner.calls.append((f"{self.label}.__enter__", (), {}))
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        self.owner.calls.append((f"{self.label}.__exit__", (exc_type, exc, tb), {}))
        return None


class ExpanderStub:
    """Record usage of expandable debug panels."""

    def __init__(self, owner: "StreamlitStub", label: str) -> None:
        self.owner = owner
        self.label = label
        self.records: list[tuple[str, Any, dict[str, Any]]] = []

    def __enter__(self) -> "ExpanderStub":
        self.owner.calls.append((f"{self.label}.__enter__", (), {}))
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        self.owner.calls.append((f"{self.label}.__exit__", (exc_type, exc, tb), {}))
        return None

    def code(self, text: str, **kwargs: Any) -> None:
        self.records.append(("code", text, kwargs))
        self.owner.calls.append((f"{self.label}.code", (text,), kwargs))


class SidebarStub:
    """Capture sidebar interactions including navigation state."""

    def __init__(self, owner: "StreamlitStub") -> None:
        self.owner = owner
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def radio(self, label: str, options: list[str], index: int = 0) -> str:
        options_list = list(options)
        self.calls.append(("radio", (label, options_list, index), {}))
        self.owner.calls.append(("sidebar.radio", (label, options_list, index), {}))
        if self.owner.sidebar_selection is not None:
            return self.owner.sidebar_selection
        return options_list[index]

    def title(self, text: str) -> None:
        self.calls.append(("title", (text,), {}))
        self.owner.calls.append(("sidebar.title", (text,), {}))

    def markdown(self, text: str, **kwargs: Any) -> None:
        self.calls.append(("markdown", (text,), kwargs))
        self.owner.calls.append(("sidebar.markdown", (text,), kwargs))


class StreamlitStub:
    """Purpose-built Streamlit replacement for exercising WebUI behavior."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []
        self.import_requests = 0
        self.sidebar_selection: str | None = None
        self.session_state = SessionState()
        self.sidebar = SidebarStub(self)
        self.components = SimpleNamespace(
            v1=SimpleNamespace(html=self._record("components.v1.html"))
        )
        self.progress_bars: list[ProgressBarStub] = []
        self.empty_containers: list[ContainerStub] = []
        self.containers: list[ContainerStub] = []
        self.expanders: list[ExpanderStub] = []
        self._empty_count = 0
        self._container_count = 0
        self._expander_count = 0
        self._progress_count = 0

    def _record(self, name: str) -> Callable[..., None]:
        def recorder(*args: Any, **kwargs: Any) -> None:
            self.calls.append((name, args, kwargs))

        return recorder

    def set_page_config(self, *args: Any, **kwargs: Any) -> None:
        self.calls.append(("set_page_config", args, kwargs))

    def markdown(self, *args: Any, **kwargs: Any) -> None:
        self.calls.append(("markdown", args, kwargs))

    def write(self, *args: Any, **kwargs: Any) -> None:
        self.calls.append(("write", args, kwargs))

    def error(self, *args: Any, **kwargs: Any) -> None:
        self.calls.append(("error", args, kwargs))

    def warning(self, *args: Any, **kwargs: Any) -> None:
        self.calls.append(("warning", args, kwargs))

    def success(self, *args: Any, **kwargs: Any) -> None:
        self.calls.append(("success", args, kwargs))

    def info(self, *args: Any, **kwargs: Any) -> None:
        self.calls.append(("info", args, kwargs))

    def header(self, *args: Any, **kwargs: Any) -> None:
        self.calls.append(("header", args, kwargs))

    def subheader(self, *args: Any, **kwargs: Any) -> None:
        self.calls.append(("subheader", args, kwargs))

    def empty(self) -> ContainerStub:
        label = f"empty[{self._empty_count}]"
        self._empty_count += 1
        container = ContainerStub(self, label)
        self.empty_containers.append(container)
        self.calls.append(("empty", (), {}))
        return container

    def progress(self, value: float) -> ProgressBarStub:
        label = f"progress[{self._progress_count}]"
        self._progress_count += 1
        bar = ProgressBarStub(self, label)
        self.progress_bars.append(bar)
        self.calls.append(("progress", (value,), {}))
        return bar

    def container(self) -> ContainerStub:
        label = f"container[{self._container_count}]"
        self._container_count += 1
        container = ContainerStub(self, label)
        self.containers.append(container)
        self.calls.append(("container", (), {}))
        return container

    def expander(self, label: str, *, expanded: bool = False) -> ExpanderStub:
        expander_label = f"expander[{self._expander_count}]"
        self._expander_count += 1
        expander = ExpanderStub(self, expander_label)
        self.expanders.append(expander)
        self.calls.append(("expander", (label,), {"expanded": expanded}))
        return expander


@pytest.fixture
def streamlit_stub(monkeypatch: pytest.MonkeyPatch) -> StreamlitStub:
    """Install a deterministic Streamlit stub for the duration of a test."""

    stub = StreamlitStub()
    original_import = importlib.import_module

    def fake_import(name: str, package: str | None = None):
        if name == "streamlit":
            stub.import_requests += 1
            return stub
        return original_import(name, package)

    monkeypatch.setattr(webui, "_STREAMLIT", None)
    monkeypatch.setattr(importlib, "import_module", fake_import)
    return stub


def test_lazy_loader_imports_streamlit_stub_once(streamlit_stub: StreamlitStub) -> None:
    """Accessing the lazy proxy imports the stub a single time."""

    webui.st.write("hello")
    assert streamlit_stub.import_requests == 1
    webui.st.success("done")
    assert streamlit_stub.import_requests == 1
    assert ("write", ("hello",), {}) in streamlit_stub.calls
    assert ("success", ("done",), {}) in streamlit_stub.calls


def test_missing_streamlit_surfaces_install_guidance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Import failures raise DevSynthError with installation instructions."""

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


def test_display_result_sanitizes_error_output(
    streamlit_stub: StreamlitStub, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Error rendering escapes HTML and surfaces docs and suggestions."""

    ui = webui.WebUI()

    monkeypatch.setattr(
        webui.WebUI, "_get_error_type", lambda self, message: "api_error"
    )
    monkeypatch.setattr(
        webui.WebUI,
        "_get_error_suggestions",
        lambda self, error_type: ["Check API token", "Retry request"],
    )
    monkeypatch.setattr(
        webui.WebUI,
        "_get_documentation_links",
        lambda self, error_type: {"API Integration Guide": "https://docs.invalid/api"},
    )

    ui.display_result("<script>alert</script>", message_type="error")

    assert streamlit_stub.calls == [
        ("error", ("",), {}),
        ("markdown", ("**Suggestions:**",), {}),
        ("markdown", ("- Check API token",), {}),
        ("markdown", ("- Retry request",), {}),
        ("markdown", ("**Documentation:**",), {}),
        (
            "markdown",
            ("- [API Integration Guide](https://docs.invalid/api)",),
            {},
        ),
    ]


def test_ui_progress_tracks_status_and_subtasks(streamlit_stub: StreamlitStub) -> None:
    """Progress updates sanitize status text and orchestrate subtasks."""

    ui = webui.WebUI()
    progress = ui.create_progress("<b>Main task</b>", total=4)

    status_container = streamlit_stub.empty_containers[0]
    assert status_container.records[0][1] == "**&lt;b&gt;Main task&lt;/b&gt;** - 0%"

    progress.update(advance=2, description="<i>Phase</i>")

    assert status_container.records[-1][1] == "**&lt;i&gt;Phase&lt;/i&gt;** - 50%"
    main_bar = streamlit_stub.progress_bars[0]
    assert pytest.approx(main_bar.values[-1]) == 0.5

    subtask_id = progress.add_subtask("<tag>Subtask</tag>", total=2)
    sub_container = streamlit_stub.containers[0]
    assert any(
        record
        == (
            "markdown",
            "&nbsp;&nbsp;&nbsp;&nbsp;**&lt;tag&gt;Subtask&lt;/tag&gt;** - 0%",
            {},
        )
        for record in sub_container.records
    )

    progress.update_subtask(subtask_id, advance=1, description="<u>Halfway</u>")
    assert any(
        record
        == (
            "markdown",
            "&nbsp;&nbsp;&nbsp;&nbsp;**&lt;u&gt;Halfway&lt;/u&gt;** - 50%",
            {},
        )
        for record in sub_container.records
    )

    progress.complete_subtask(subtask_id)
    assert any(
        record
        == (
            "markdown",
            "&nbsp;&nbsp;&nbsp;&nbsp;**&lt;u&gt;Halfway&lt;/u&gt;** - 100%",
            {},
        )
        for record in sub_container.records
    )
    assert (
        "container[0].success",
        ("Completed: &lt;u&gt;Halfway&lt;/u&gt;",),
        {},
    ) in streamlit_stub.calls

    progress.complete()
    assert main_bar.values[-1] == 1.0
    assert (
        "success",
        ("Completed: &lt;i&gt;Phase&lt;/i&gt;",),
        {},
    ) in streamlit_stub.calls


def test_router_run_uses_default_and_persists_selection(
    streamlit_stub: StreamlitStub, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Router defaults to the first page and stores the last selection."""

    selected: list[str] = []

    def onboarding() -> None:
        selected.append("Onboarding")

    def docs() -> None:
        selected.append("Docs")

    monkeypatch.setattr(
        webui.WebUI,
        "navigation_items",
        lambda self: {"Onboarding": onboarding, "Docs": docs},
    )

    ui = webui.WebUI()
    router = ui._ensure_router()

    router.run()
    assert selected == ["Onboarding"]
    assert streamlit_stub.session_state.nav == "Onboarding"

    streamlit_stub.sidebar_selection = "Docs"
    router.run()
    assert selected[-1] == "Docs"
    assert streamlit_stub.session_state.nav == "Docs"


def test_webui_run_configures_router_and_layout(
    streamlit_stub: StreamlitStub, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``WebUI.run`` wires the router and applies responsive defaults."""

    layout = {
        "columns": 2,
        "sidebar_width": "30%",
        "content_width": "70%",
        "font_size": "medium",
        "padding": "1rem",
        "is_mobile": False,
    }
    monkeypatch.setattr(webui.WebUI, "get_layout_config", lambda self: layout)

    pages = {"Docs": lambda: None}
    monkeypatch.setattr(webui.WebUI, "navigation_items", lambda self: pages)

    router_calls: list[dict[str, Any]] = []

    class RouterSpy:
        def __init__(
            self,
            ui: webui.WebUI,
            pages_arg: dict[str, Callable[[], None]],
            *,
            default=None,
        ) -> None:
            router_calls.append(
                {"ui": ui, "pages": pages_arg, "default": default, "run": False}
            )

        def run(self) -> None:
            router_calls[-1]["run"] = True

    monkeypatch.setattr(webui, "Router", RouterSpy)

    ui = webui.WebUI()
    ui.run()

    assert streamlit_stub.session_state.screen_width == 1200
    assert streamlit_stub.session_state.screen_height == 800

    css_call = next(
        call
        for call in streamlit_stub.calls
        if call[0] == "markdown" and "padding: 1rem" in call[1][0]
    )
    assert css_call[2]["unsafe_allow_html"] is True

    assert any(call[0] == "set_page_config" for call in streamlit_stub.calls)
    assert any(call[0] == "components.v1.html" for call in streamlit_stub.calls)

    assert router_calls and router_calls[0]["ui"] is ui
    assert router_calls[0]["pages"] == pages
    assert router_calls[0]["default"] is None
    assert router_calls[0]["run"] is True
