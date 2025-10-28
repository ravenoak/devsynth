from __future__ import annotations

"""Dear PyGUI implementation of :class:`UXBridge`.

This bridge provides a minimal user interaction layer built on top of
``dearpygui``.  The implementation mirrors the behaviour of other bridges in
the project, exposing synchronous methods for prompting users, confirming
choices and displaying results.  Each interaction runs inside a simple Dear
PyGUI event loop and uses safe text handling utilities provided by the
project.
"""

import threading
from typing import Any, Optional
from collections.abc import Callable, Sequence

# Lazy import: resolved in __init__ to allow tests to stub dearpygui safely
# and to avoid loading the native extension during test collection.
dpg = None  # type: ignore

from .shared_bridge import SharedBridgeMixin
from .ux_bridge import ProgressIndicator, UXBridge, sanitize_output


class DearPyGUIProgressIndicator(ProgressIndicator):
    """Progress indicator backed by a Dear PyGUI progress bar."""

    def __init__(
        self, description: str, total: int, *, cancellable: bool = False
    ) -> None:
        self._total = float(total)
        self._current = 0.0
        self._cancelled = threading.Event()
        self._window = dpg.window(label=sanitize_output(description))
        with self._window:
            self._bar_id = dpg.add_progress_bar(default_value=0.0)
            self._status_id = dpg.add_text("Starting...")
            if cancellable:
                dpg.add_button(label="Cancel", callback=self.cancel)

    def update(
        self,
        *,
        advance: float = 1,
        description: str | None = None,
        status: str | None = None,
    ) -> None:
        self._current += advance
        if description is not None:
            dpg.set_item_label(self._window, sanitize_output(str(description)))

        if status is not None:
            dpg.set_value(self._status_id, sanitize_output(str(status)))
        else:
            pct = self._current / self._total if self._total else 0
            if pct >= 1:
                msg = "Complete"
            elif pct >= 0.99:
                msg = "Finalizing..."
            elif pct >= 0.75:
                msg = "Almost done..."
            elif pct >= 0.5:
                msg = "Halfway there..."
            elif pct >= 0.25:
                msg = "Processing..."
            else:
                msg = "Starting..."
            dpg.set_value(self._status_id, msg)

        dpg.set_value(self._bar_id, min(self._current / self._total, 1.0))
        dpg.render_dearpygui_frame()

    def complete(self) -> None:
        dpg.set_value(self._bar_id, 1.0)
        dpg.set_value(self._status_id, "Complete")
        dpg.render_dearpygui_frame()
        dpg.delete_item(self._window)

    # ------------------------------------------------------------------
    # Cancellation helpers
    # ------------------------------------------------------------------
    def cancel(self) -> None:
        """Request cancellation of the running operation."""

        self._cancelled.set()

    def is_cancelled(self) -> bool:
        """Return whether cancellation has been requested."""

        return self._cancelled.is_set()


class DearPyGUIBridge(SharedBridgeMixin, UXBridge):
    """UXBridge implementation using Dear PyGUI widgets."""

    def __init__(self) -> None:
        super().__init__()
        # Lazy import to avoid loading native extension during test collection
        # and to allow tests to stub dearpygui before instantiation.
        global dpg
        if dpg is None:
            try:
                import importlib

                dpg = importlib.import_module("dearpygui.dearpygui")
            except Exception as exc:  # pragma: no cover - optional during tests
                raise RuntimeError("dearpygui is required for DearPyGUIBridge") from exc
        if not getattr(dpg, "is_viewport_created", lambda: False)():
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
        choices: Sequence[str] | None = None,
        default: str | None = None,
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
        self, description: str, *, total: int = 100, cancellable: bool = False
    ) -> ProgressIndicator:
        return DearPyGUIProgressIndicator(description, total, cancellable=cancellable)

    # ------------------------------------------------------------------
    # Command helpers
    # ------------------------------------------------------------------
    def run_cli_command(
        self,
        cmd: Callable[..., Any],
        *,
        description: str | None = None,
        cancellable: bool = False,
        message_type: str = "error",
        progress_hook: Callable[[ProgressIndicator], None] | None = None,
        error_hook: Callable[[BaseException], None] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Execute a potentially blocking CLI command.

        The command is executed in a background thread while this method polls
        ``render_dearpygui_frame`` to keep the UI responsive.  Optional hooks
        allow callers to update progress or handle errors manually.  Any
        unhandled exceptions are displayed via :meth:`display_result` using the
        provided ``message_type``.

        Args:
            cmd: Callable representing the CLI command.
            description: Optional description for the progress indicator.
            cancellable: Whether to show a cancel button.
            message_type: Message type used if an exception occurs.
            progress_hook: Optional callable invoked every UI poll with the
                :class:`ProgressIndicator`.
            error_hook: Optional callable invoked with any caught exception
                instead of displaying it directly.
            **kwargs: Additional keyword arguments passed to ``cmd``.

        Returns:
            The result returned by ``cmd`` or ``None`` if an error occurred.
        """

        prog_desc = description or f"Running {getattr(cmd, '__name__', 'command')}"
        progress = self.create_progress(prog_desc, cancellable=cancellable)

        result: list[Any] = []
        error: list[BaseException] = []
        done = threading.Event()
        cancelled = threading.Event()

        def _target() -> None:
            try:
                result.append(cmd(**kwargs))
            except BaseException as exc:  # pragma: no cover - defensive
                error.append(exc)
            finally:
                done.set()

        threading.Thread(target=_target, daemon=True).start()

        while True:
            if cancellable and progress.is_cancelled():
                cancelled.set()
            if done.is_set() or cancelled.is_set():
                break
            if progress_hook is not None:
                progress_hook(progress)
            dpg.render_dearpygui_frame()

        progress.complete()

        if error:
            exc = error[0]
            if error_hook is not None:
                error_hook(exc)
            else:
                self.display_result(
                    sanitize_output(str(exc)), message_type=message_type
                )
            return None

        if cancelled.is_set():
            return None

        return result[0] if result else None


__all__ = ["DearPyGUIBridge", "DearPyGUIProgressIndicator"]
