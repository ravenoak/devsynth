"""Test doubles for Streamlit interactions."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any


class FakeSessionState(dict):
    """Dictionary-like session state supporting attribute access."""

    def __getattr__(self, item: str) -> Any:
        try:
            return self[item]
        except KeyError as exc:  # pragma: no cover - defensive fallback
            raise AttributeError(item) from exc

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value


class FakeStreamlit:
    """Lightweight Streamlit replacement capturing WebUI interactions."""

    def __init__(self) -> None:
        self.session_state = FakeSessionState()
        self.markdown_calls: list[tuple[str, dict[str, Any]]] = []
        self.write_calls: list[str] = []
        self.error_calls: list[str] = []
        self.info_calls: list[str] = []
        self.success_calls: list[str] = []
        self.warning_calls: list[str] = []
        self.header_calls: list[str] = []
        self.subheader_calls: list[str] = []
        self.components_html_calls: list[tuple[str, dict[str, Any]]] = []
        self.sidebar_title_calls: list[str] = []
        self.sidebar_markdown_calls: list[tuple[str, dict[str, Any]]] = []
        self.sidebar_radio_calls: list[tuple[str, tuple[str, ...], int]] = []
        self.set_page_config_calls: list[dict[str, Any]] = []
        self.set_page_config_exception: Exception | None = None
        self.sidebar_radio_selection: str | None = None

        self.components = SimpleNamespace(
            v1=SimpleNamespace(html=self._components_html)
        )
        self.sidebar = SimpleNamespace(
            title=self._sidebar_title,
            markdown=self._sidebar_markdown,
            radio=self._sidebar_radio,
        )

    # ------------------------------------------------------------------
    # Streamlit primitives
    # ------------------------------------------------------------------
    def set_page_config(self, **kwargs: Any) -> None:
        self.set_page_config_calls.append(kwargs)
        if self.set_page_config_exception is not None:
            raise self.set_page_config_exception

    def markdown(self, content: str, **kwargs: Any) -> None:
        self.markdown_calls.append((content, kwargs))

    def write(self, content: str) -> None:
        self.write_calls.append(content)

    def error(self, content: str) -> None:
        self.error_calls.append(content)

    def info(self, content: str) -> None:
        self.info_calls.append(content)

    def success(self, content: str) -> None:
        self.success_calls.append(content)

    def warning(self, content: str) -> None:
        self.warning_calls.append(content)

    def header(self, content: str) -> None:
        self.header_calls.append(content)

    def subheader(self, content: str) -> None:
        self.subheader_calls.append(content)

    # ------------------------------------------------------------------
    # Sidebar helpers
    # ------------------------------------------------------------------
    def _sidebar_title(self, text: str) -> None:
        self.sidebar_title_calls.append(text)

    def _sidebar_markdown(self, text: str, **kwargs: Any) -> None:
        self.sidebar_markdown_calls.append((text, kwargs))

    def _sidebar_radio(self, label: str, options: list[str], index: int = 0) -> str:
        self.sidebar_radio_calls.append((label, tuple(options), index))
        if self.sidebar_radio_selection is not None:
            return self.sidebar_radio_selection
        return options[index]

    # ------------------------------------------------------------------
    # Components
    # ------------------------------------------------------------------
    def _components_html(self, content: str, **kwargs: Any) -> None:
        self.components_html_calls.append((content, kwargs))


__all__ = ["FakeSessionState", "FakeStreamlit"]
