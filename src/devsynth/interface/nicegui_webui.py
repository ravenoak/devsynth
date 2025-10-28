"""NiceGUI implementation of the DevSynth WebUI.

This module mirrors the navigation logic of :mod:`devsynth.interface.webui`
using the NiceGUI framework. It exposes a ``main`` function which can be
invoked similarly to ``streamlit run`` to start the application.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from collections.abc import Callable, Sequence

try:
    from nicegui import app, ui

    _HAS_NICEGUI = True
except Exception:  # pragma: no cover - optional dependency not installed
    app = None  # type: ignore
    ui = None  # type: ignore
    _HAS_NICEGUI = False

from devsynth.interface.progress_utils import run_with_progress
from devsynth.interface.shared_bridge import SharedBridgeMixin
from devsynth.interface.ux_bridge import ProgressIndicator, UXBridge, sanitize_output

_session_store: dict[str, Any] = {}


def _require_nicegui() -> None:
    """Ensure NiceGUI is available, otherwise raise a friendly error.

    This prevents accidental import-time crashes in environments where the
    optional GUI dependency is not installed (e.g., CI, headless tests).
    """
    if not _HAS_NICEGUI:
        raise RuntimeError(
            "NiceGUI is not installed. Install with 'poetry install --extras gui' "
            "or 'pip install devsynth[gui]' to enable the WebUI."
        )


class NiceGUIProgressIndicator(ProgressIndicator):
    """Simple progress bar using NiceGUI widgets.

    If NiceGUI is not available, this becomes a no-op indicator so callers can
    still execute code paths (e.g., tests) without GUI dependencies.
    """

    def __init__(self, description: str, total: int) -> None:
        self._total = total
        self._current = 0
        if _HAS_NICEGUI and ui is not None:
            with ui.row().classes("items-center"):
                self.label = ui.label(description)
                self.bar = ui.linear_progress(value=0)
        else:
            self.label = None  # type: ignore[assignment]
            self.bar = None  # type: ignore[assignment]

    def update(
        self,
        *,
        advance: float = 1,
        description: str | None = None,
        status: str | None = None,
    ) -> None:
        self._current += advance
        if _HAS_NICEGUI and self.label is not None and self.bar is not None:  # type: ignore[truthy-bool]
            if description is not None:
                self.label.text = sanitize_output(str(description))
            self.bar.value = min(1.0, self._current / float(self._total))

    def complete(self) -> None:
        if _HAS_NICEGUI and self.bar is not None:
            self.bar.value = 1


class NiceGUIBridge(SharedBridgeMixin, UXBridge):
    """Bridge implementation using NiceGUI components."""

    def __init__(self) -> None:
        self.messages: list[str] = []
        super().__init__()

    def ask_question(
        self,
        message: str,
        *,
        choices: Sequence[str] | None = None,
        default: str | None = None,
        show_default: bool = True,
    ) -> str:
        return str(default or "")

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        return default

    def display_result(
        self, message: str, *, highlight: bool = False, message_type: str = None
    ) -> None:
        formatted = self._format_for_output(
            message, highlight=highlight, message_type=message_type
        )
        if _HAS_NICEGUI:
            try:
                ui.notify(formatted, type=message_type or "info")
            except Exception:
                # Fallback to message buffer if UI notification fails
                pass
        self.messages.append(str(formatted))

    def create_progress(
        self, description: str, *, total: int = 100
    ) -> ProgressIndicator:
        return NiceGUIProgressIndicator(description, total)

    @staticmethod
    def get_session_value(key: str, default=None):
        try:
            if not _HAS_NICEGUI or app is None:
                raise RuntimeError("NiceGUI not available")
            return app.storage.user.get(key, default)
        except Exception:
            return _session_store.get(key, default)

    @staticmethod
    def set_session_value(key: str, value) -> None:
        try:
            if not _HAS_NICEGUI or app is None:
                raise RuntimeError("NiceGUI not available")
            app.storage.user[key] = value
        except Exception:
            _session_store[key] = value


# ---------------------------------------------------------------------------
# Application setup
# ---------------------------------------------------------------------------


def _cli(name: str):
    """Return a CLI command by name if available."""
    try:  # pragma: no cover - optional dependency handling
        import importlib

        _cli_mod = importlib.import_module("devsynth.application.cli")  # type: ignore
        return getattr(_cli_mod, name)
    except Exception:  # pragma: no cover
        return None


def _placeholder_run(name: str, bridge: UXBridge) -> None:
    """Run a placeholder command showing progress."""
    import time

    def work() -> None:
        for _ in range(5):
            time.sleep(0.1)

    run_with_progress(work, bridge, f"Running {name}")
    bridge.display_result(f"{name} finished", message_type="success")


NAV_ITEMS: dict[str, Callable[[UXBridge], None]] = {
    "Onboarding": lambda b: (_cli("init_cmd") or _placeholder_run)("Onboarding", b),
    "Requirements": lambda b: (_cli("spec_cmd") or _placeholder_run)("Requirements", b),
    "Analysis": lambda b: _placeholder_run("Analysis", b),
    "Synthesis": lambda b: _placeholder_run("Synthesis", b),
    "EDRR Cycle": lambda b: _placeholder_run("EDRR Cycle", b),
    "Alignment": lambda b: _placeholder_run("Alignment", b),
    "Alignment Metrics": lambda b: _placeholder_run("Alignment Metrics", b),
    "Inspect Config": lambda b: _placeholder_run("Inspect Config", b),
    "Validate Manifest": lambda b: _placeholder_run("Validate Manifest", b),
    "Validate Metadata": lambda b: _placeholder_run("Validate Metadata", b),
    "Test Metrics": lambda b: _placeholder_run("Test Metrics", b),
    "Generate Docs": lambda b: _placeholder_run("Generate Docs", b),
    "Ingest": lambda b: _placeholder_run("Ingest", b),
    "API Spec": lambda b: _placeholder_run("API Spec", b),
    "Refactor": lambda b: _placeholder_run("Refactor", b),
    "Web App": lambda b: _placeholder_run("Web App", b),
    "Serve": lambda b: _placeholder_run("Serve", b),
    "DB Schema": lambda b: _placeholder_run("DB Schema", b),
    "Config": lambda b: _placeholder_run("Config", b),
    "Doctor": lambda b: _placeholder_run("Doctor", b),
    "Diagnostics": lambda b: _placeholder_run("Diagnostics", b),
}


def _slug(name: str) -> str:
    return name.lower().replace(" ", "-")


def _render_nav() -> None:
    with ui.left_drawer().classes("bg-grey-2"):
        ui.label("DevSynth")
        for name in NAV_ITEMS:
            ui.link(name, f"/{_slug(name)}")


def _register_pages(bridge: NiceGUIBridge) -> None:
    _require_nicegui()
    for name, handler in NAV_ITEMS.items():
        path = "/" + _slug(name)

        @ui.page(path)
        def _page(handler=handler, name=name):  # type: ignore[misc]
            bridge.set_session_value("nav", name)
            _render_nav()
            ui.label(name).classes("text-h5")
            ui.button(
                "Run",
                on_click=lambda handler=handler: handler(bridge),
            )

    @ui.page("/")
    def _index():  # pragma: no cover - simple redirect
        nav = bridge.get_session_value("nav", list(NAV_ITEMS)[0])
        ui.navigate.to(f"/{_slug(nav)}")


def main() -> None:
    """Launch the NiceGUI WebUI."""
    _require_nicegui()
    bridge = NiceGUIBridge()
    _register_pages(bridge)
    ui.run()


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
