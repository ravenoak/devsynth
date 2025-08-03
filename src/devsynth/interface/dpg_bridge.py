from __future__ import annotations

"""Dear PyGUI implementation of :class:`UXBridge`.

This bridge provides a minimal user interaction layer built on top of
`dearpygui`.  The implementation mirrors the behaviour of other bridges in the
project, exposing synchronous methods for prompting users, confirming choices
and displaying results.  Each interaction runs inside a simple Dear PyGUI event
loop and uses safe text handling utilities provided by the project.
"""

from typing import Optional, Sequence

try:  # pragma: no cover - dearpygui may not be installed during tests
    import dearpygui.dearpygui as dpg
except Exception:  # pragma: no cover - gracefully handle missing dependency
    dpg = None  # type: ignore

from .shared_bridge import SharedBridgeMixin
from .ux_bridge import ProgressIndicator, UXBridge, sanitize_output


class DearPyGUIProgressIndicator(ProgressIndicator):
    """Simple progress indicator backed by a Dear PyGUI progress bar."""

    def __init__(self, description: str, total: int) -> None:
        self._total = float(total)
        self._current = 0.0
        self._window = dpg.window(label=sanitize_output(description))
        with self._window:
            self._bar_id = dpg.add_progress_bar(default_value=0.0)

    def update(self, *, advance: float = 1, description: Optional[str] = None) -> None:
        self._current += advance
        if description is not None:
            dpg.set_item_label(self._window, sanitize_output(str(description)))
        dpg.set_value(self._bar_id, min(self._current / self._total, 1.0))
        dpg.render_dearpygui_frame()

    def complete(self) -> None:
        dpg.set_value(self._bar_id, 1.0)
        dpg.render_dearpygui_frame()
        dpg.delete_item(self._window)


class DearPyGUIBridge(SharedBridgeMixin, UXBridge):
    """UXBridge implementation using Dear PyGUI widgets."""

    def __init__(self) -> None:
        super().__init__()
        if dpg is None:  # pragma: no cover - defensive
            raise RuntimeError("dearpygui is required for DearPyGUIBridge")
        if not dpg.is_viewport_created():
            dpg.create_context()
            dpg.create_viewport(title="DevSynth")
            dpg.setup_dearpygui()
            dpg.show_viewport()

    # ------------------------------------------------------------------
    # Interaction helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _event_loop(condition) -> None:
        """Run a small event loop until *condition* returns True."""

        while not condition():
            dpg.render_dearpygui_frame()

    # ------------------------------------------------------------------
    # UXBridge interface
    # ------------------------------------------------------------------
    def ask_question(
        self,
        message: str,
        *,
        choices: Optional[Sequence[str]] = None,
        default: Optional[str] = None,
        show_default: bool = True,
    ) -> str:
        formatted = self._format_for_output(message)
        result: dict[str, str] = {"value": default or ""}

        with dpg.window(label="Question", modal=True) as win:
            dpg.add_text(formatted if isinstance(formatted, str) else str(formatted))
            if choices:
                for choice in choices:
                    dpg.add_selectable(
                        label=sanitize_output(choice),
                        callback=lambda s, a, c=choice: (
                            result.update(value=c),
                            dpg.delete_item(win),
                        ),
                    )
            else:
                input_id = dpg.add_input_text(
                    default_value=default or "",
                    on_enter=True,
                    callback=lambda s, a: (
                        result.update(value=a),
                        dpg.delete_item(win),
                    ),
                )
                dpg.add_button(
                    label="Submit",
                    callback=lambda: (
                        result.update(value=dpg.get_value(input_id)),
                        dpg.delete_item(win),
                    ),
                )

        self._event_loop(lambda: not dpg.does_item_exist(win))
        return result["value"]

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        formatted = self._format_for_output(message)
        result: dict[str, bool] = {"value": default}

        with dpg.window(label="Confirm", modal=True) as win:
            dpg.add_text(formatted if isinstance(formatted, str) else str(formatted))

            def _yes() -> None:
                result["value"] = True
                dpg.delete_item(win)

            def _no() -> None:
                result["value"] = False
                dpg.delete_item(win)

            dpg.add_button(label="Yes", callback=_yes)
            dpg.add_button(label="No", callback=_no)

        self._event_loop(lambda: not dpg.does_item_exist(win))
        return result["value"]

    def display_result(
        self,
        message: str,
        *,
        highlight: bool = False,
        message_type: str | None = None,
    ) -> None:
        formatted = self._format_for_output(
            message, highlight=highlight, message_type=message_type
        )
        text = (
            formatted if isinstance(formatted, str) else sanitize_output(str(formatted))
        )

        with dpg.window(label="Result", modal=True) as win:
            dpg.add_text(text)
            dpg.add_button(label="OK", callback=lambda: dpg.delete_item(win))

        self._event_loop(lambda: not dpg.does_item_exist(win))

    def create_progress(
        self, description: str, *, total: int = 100
    ) -> ProgressIndicator:
        return DearPyGUIProgressIndicator(description, total)


__all__ = ["DearPyGUIBridge", "DearPyGUIProgressIndicator"]
