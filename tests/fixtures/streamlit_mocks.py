"""Typed facades for Streamlit test doubles used throughout the suite."""

from __future__ import annotations

from types import ModuleType
from typing import Any, Literal, Protocol, cast
from unittest.mock import MagicMock


class DummyContext:
    """Simple context manager used for streamlit forms/spinners."""

    def __init__(self, submitted: bool = True):
        self.submitted = submitted

    def __enter__(self) -> DummyContext:
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc: BaseException | None,
        _tb: Any,
    ) -> Literal[False]:
        return False

    def form_submit_button(self, *_args: Any, **_kwargs: Any) -> bool:
        return self.submitted

    def button(self, *_args: Any, **_kwargs: Any) -> bool:
        return self.submitted


class StreamlitSessionState(dict[str, Any]):
    """Dictionary-like session state supporting attribute access."""

    def __getattr__(self, name: str) -> Any:
        if name in self:
            return self[name]
        raise AttributeError(name)

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


class StreamlitComponentsV1(Protocol):
    """Subset of ``streamlit.components.v1`` APIs used in tests."""

    html: MagicMock


class StreamlitComponents(Protocol):
    """Protocol describing the ``st.components`` namespace."""

    v1: StreamlitComponentsV1


class StreamlitSidebar(Protocol):
    """Protocol for the sidebar namespace exposed by Streamlit."""

    title: MagicMock
    markdown: MagicMock
    radio: MagicMock
    button: MagicMock
    selectbox: MagicMock
    checkbox: MagicMock
    text_input: MagicMock
    text_area: MagicMock
    expander: MagicMock


class StreamlitModule(Protocol):
    """Typed interface for the Streamlit module stub used in tests."""

    session_state: StreamlitSessionState
    header: MagicMock
    subheader: MagicMock
    text_input: MagicMock
    text_area: MagicMock
    selectbox: MagicMock
    multiselect: MagicMock
    checkbox: MagicMock
    radio: MagicMock
    number_input: MagicMock
    toggle: MagicMock
    button: MagicMock
    form_submit_button: MagicMock
    expander: MagicMock
    form: MagicMock
    spinner: MagicMock
    divider: MagicMock
    columns: MagicMock
    progress: MagicMock
    write: MagicMock
    markdown: MagicMock
    code: MagicMock
    error: MagicMock
    info: MagicMock
    success: MagicMock
    warning: MagicMock
    set_page_config: MagicMock
    empty: MagicMock
    container: MagicMock
    components: StreamlitComponents
    sidebar: StreamlitSidebar
    experimental_rerun: MagicMock
    tabs: MagicMock
    caption: MagicMock
    slider: MagicMock
    select_slider: MagicMock
    date_input: MagicMock
    time_input: MagicMock
    file_uploader: MagicMock
    color_picker: MagicMock


class _ComponentsV1Facade(StreamlitComponentsV1):
    """Concrete implementation of :class:`StreamlitComponentsV1`."""

    def __init__(self) -> None:
        self.html: MagicMock = MagicMock()


class _ComponentsFacade(StreamlitComponents):
    """Namespace facade for ``st.components``."""

    def __init__(self) -> None:
        self.v1: _ComponentsV1Facade = _ComponentsV1Facade()


class _SidebarFacade(StreamlitSidebar):
    """Concrete sidebar implementation satisfying :class:`StreamlitSidebar`."""

    def __init__(self, submitted: bool) -> None:
        self.title: MagicMock = MagicMock()
        self.markdown: MagicMock = MagicMock()
        self.radio: MagicMock = MagicMock(return_value="Onboarding")
        self.button: MagicMock = MagicMock(return_value=False)
        self.selectbox: MagicMock = MagicMock(return_value="test")
        self.checkbox: MagicMock = MagicMock(return_value=False)
        self.text_input: MagicMock = MagicMock(return_value="test")
        self.text_area: MagicMock = MagicMock(return_value="test")
        self.expander: MagicMock = MagicMock(return_value=DummyContext(submitted))


class StreamlitStub(ModuleType):
    """Concrete module stub implementing the :class:`StreamlitModule` protocol."""

    def __init__(self, submitted: bool = True) -> None:
        super().__init__("streamlit")
        self.session_state: StreamlitSessionState = StreamlitSessionState()
        self.session_state.wizard_step = 0

        self.header: MagicMock = MagicMock()
        self.subheader: MagicMock = MagicMock()
        self.text_input: MagicMock = MagicMock(return_value="text")
        self.text_area: MagicMock = MagicMock(return_value="desc")
        self.selectbox: MagicMock = MagicMock(return_value="choice")
        self.multiselect: MagicMock = MagicMock(return_value=[])
        self.checkbox: MagicMock = MagicMock(return_value=True)
        self.number_input: MagicMock = MagicMock(return_value=30)
        self.toggle: MagicMock = MagicMock(return_value=False)
        self.radio: MagicMock = MagicMock(return_value="choice")
        self.button: MagicMock = MagicMock(return_value=False)
        self.form_submit_button: MagicMock = MagicMock(return_value=submitted)
        self.expander: MagicMock = MagicMock(return_value=DummyContext(submitted))
        self.form: MagicMock = MagicMock(return_value=DummyContext(submitted))
        self.spinner: MagicMock = MagicMock(return_value=DummyContext(submitted))
        self.divider: MagicMock = MagicMock()
        self.columns: MagicMock = MagicMock(
            return_value=(
                MagicMock(button=lambda *a, **k: False),
                MagicMock(button=lambda *a, **k: False),
            )
        )
        self.progress: MagicMock = MagicMock()
        self.write: MagicMock = MagicMock()
        self.markdown: MagicMock = MagicMock()
        self.code: MagicMock = MagicMock()
        self.error: MagicMock = MagicMock()
        self.info: MagicMock = MagicMock()
        self.success: MagicMock = MagicMock()
        self.warning: MagicMock = MagicMock()
        self.set_page_config: MagicMock = MagicMock()
        self.empty: MagicMock = MagicMock(
            return_value=MagicMock(markdown=MagicMock(), empty=MagicMock())
        )
        self.container: MagicMock = MagicMock(return_value=DummyContext(submitted))
        self.components: StreamlitComponents = cast(
            StreamlitComponents, _ComponentsFacade()
        )
        self.sidebar: StreamlitSidebar = cast(
            StreamlitSidebar, _SidebarFacade(submitted)
        )
        self.experimental_rerun: MagicMock = MagicMock()
        self.tabs: MagicMock = MagicMock(return_value=[DummyContext(submitted)])
        self.caption: MagicMock = MagicMock()
        self.slider: MagicMock = MagicMock(return_value=0)
        self.select_slider: MagicMock = MagicMock(return_value="")
        self.date_input: MagicMock = MagicMock(return_value=None)
        self.time_input: MagicMock = MagicMock(return_value=None)
        self.file_uploader: MagicMock = MagicMock(return_value=None)
        self.color_picker: MagicMock = MagicMock(return_value="")


def make_streamlit_mock(submitted: bool = True) -> StreamlitModule:
    """Return a mocked ``streamlit`` module with common APIs used in WebUI."""

    return StreamlitStub(submitted=submitted)


__all__ = [
    "DummyContext",
    "StreamlitModule",
    "StreamlitSessionState",
    "StreamlitStub",
    "make_streamlit_mock",
]
