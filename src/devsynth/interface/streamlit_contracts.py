"""Shared Streamlit protocol definitions used by the WebUI glue code."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from contextlib import AbstractContextManager
from typing import Any, Protocol


class SessionState(Protocol):
    """Contract for the mutable session state exposed by Streamlit."""

    def __getitem__(self, key: str) -> Any: ...

    def __setitem__(self, key: str, value: Any) -> None: ...

    def get(self, key: str, default: Any | None = ...) -> Any: ...

    def __contains__(self, key: object) -> bool: ...

    def __getattr__(self, name: str) -> Any: ...

    def __setattr__(self, name: str, value: Any) -> None: ...


class Sidebar(Protocol):
    """Minimal sidebar surface consumed by DevSynth's navigation router."""

    def radio(
        self,
        label: str,
        options: Sequence[str],
        *,
        index: int | None = ...,
    ) -> str: ...

    def title(self, title: str) -> None: ...

    def markdown(self, body: str, *, unsafe_allow_html: bool = ...) -> None: ...


class ProgressBar(Protocol):
    """Progress handle returned by ``st.progress`` and column progress bars."""

    def progress(self, value: float | int) -> None: ...


class DeltaGenerator(Protocol):
    """Container-like surface returned by Streamlit layout helpers."""

    def button(self, label: str, *, key: str | None = ...) -> bool: ...

    def markdown(self, body: str, *, unsafe_allow_html: bool = ...) -> None: ...

    def write(self, *args: Any, **kwargs: Any) -> None: ...

    def progress(self, value: float | int) -> ProgressBar: ...

    def success(self, message: str) -> None: ...

    def error(self, message: str) -> None: ...

    def info(self, message: str) -> None: ...

    def warning(self, message: str) -> None: ...

    def caption(self, message: str) -> None: ...

    def json(self, obj: Any) -> None: ...


class ComponentsV1(Protocol):
    """Subset of the components API consumed by the WebUI bootstrap."""

    def html(
        self,
        body: str,
        *,
        height: int | None = ...,
        scrolling: bool | None = ...,
        key: str | None = ...,
    ) -> None: ...


class ComponentsModule(Protocol):
    v1: ComponentsV1


class StreamlitModule(Protocol):
    """High-level Streamlit interface required by the WebUI renderer."""

    sidebar: Sidebar
    session_state: SessionState
    components: ComponentsModule

    def header(self, body: str) -> None: ...

    def subheader(self, body: str) -> None: ...

    def markdown(self, body: str, *, unsafe_allow_html: bool = ...) -> None: ...

    def info(self, body: str) -> None: ...

    def warning(self, body: str) -> None: ...

    def error(self, body: str) -> None: ...

    def success(self, body: str) -> None: ...

    def write(self, *args: Any, **kwargs: Any) -> None: ...

    def selectbox(
        self,
        label: str,
        options: Sequence[str],
        *,
        index: int | None = ...,
        key: str | None = ...,
    ) -> str: ...

    def checkbox(
        self, label: str, *, value: bool = ..., key: str | None = ...
    ) -> bool: ...

    def text_input(
        self,
        label: str,
        value: str = ...,
        *,
        key: str | None = ...,
    ) -> str: ...

    def text_area(
        self,
        label: str,
        value: str = ...,
        *,
        height: int | None = ...,
        key: str | None = ...,
    ) -> str: ...

    def form(self, key: str) -> AbstractContextManager[None]: ...

    def form_submit_button(self, label: str, *, type: str | None = ...) -> bool: ...

    def button(self, label: str, *, key: str | None = ...) -> bool: ...

    def spinner(self, text: str) -> AbstractContextManager[None]: ...

    def columns(self, spec: int | Iterable[float]) -> Sequence[DeltaGenerator]: ...

    def container(self) -> DeltaGenerator: ...

    def progress(self, value: float | int) -> ProgressBar: ...

    def caption(self, message: str) -> None: ...

    def json(self, obj: Any) -> None: ...

    def divider(self) -> None: ...

    def set_page_config(
        self, *, page_title: str | None = ..., layout: str | None = ...
    ) -> None: ...

    def code(self, body: str, *, language: str | None = ...) -> None: ...
