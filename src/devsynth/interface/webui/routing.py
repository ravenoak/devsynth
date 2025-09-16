from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any


class Router:
    """Handle Streamlit navigation for the WebUI."""

    def __init__(
        self,
        ui: Any,
        pages: Mapping[str, Callable[[], None]],
        *,
        default: str | None = None,
    ) -> None:
        if not pages:
            raise ValueError("Router requires at least one page")

        self._ui = ui
        self._pages = dict(pages)
        self._default = default or next(iter(pages))

    @property
    def pages(self) -> Mapping[str, Callable[[], None]]:
        return dict(self._pages)

    def run(self) -> None:
        st = self._ui.streamlit
        nav_list = list(self._pages)
        session_state = getattr(st, "session_state", None)
        stored_nav = self._default
        if session_state is not None:
            stored_nav = getattr(session_state, "nav", self._default)
        if stored_nav not in self._pages:
            stored_nav = self._default
        try:
            index = nav_list.index(stored_nav)
        except ValueError:  # pragma: no cover - defensive
            index = 0
        try:
            selected = st.sidebar.radio("Navigation", nav_list, index=index)
        except Exception as exc:  # noqa: BLE001
            self._ui.display_result(f"ERROR: {exc}")
            return

        if session_state is not None:
            session_state.nav = selected
            if hasattr(session_state, "__setitem__"):
                session_state["nav"] = selected

        page = self._pages.get(selected)
        if page is None:
            self._ui.display_result("ERROR: Invalid navigation option")
            return

        try:
            page()
        except Exception as exc:  # noqa: BLE001
            self._ui.display_result(f"ERROR: {exc}")


__all__ = ["Router"]
