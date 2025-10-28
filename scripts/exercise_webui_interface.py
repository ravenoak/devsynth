"""Manual WebUI exercise to ensure coverage captures key pathways."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from types import SimpleNamespace

COVERAGE_MODE = os.getenv("DEVSYNTH_WEBUI_COVERAGE") == "1"

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = str(ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.append(SRC_PATH)


class FakeStreamlit:
    def __init__(self) -> None:
        self.write_messages: list[str] = []
        self.info_messages: list[str] = []
        self.success_messages: list[str] = []
        self.warning_messages: list[str] = []
        self.error_messages: list[str] = []
        self.markdown_calls: list[tuple[str, dict[str, object]]] = []
        self.header_calls: list[str] = []
        self.subheader_calls: list[str] = []
        self.code_calls: list[tuple[str, dict[str, object]]] = []
        self.checkbox_values: dict[str, bool] = {}
        self.selectbox_values: dict[str, str] = {}
        self.text_inputs: dict[str, str] = {}
        self.session_state: SimpleNamespace = SimpleNamespace()
        self.empty_placeholders: list[_Placeholder] = []
        self.progress_bars: list[_ProgressBar] = []
        self.container_entries: list[_Container] = []

    # Streamlit output APIs
    def write(self, message: str) -> None:
        self.write_messages.append(message)

    def info(self, message: str) -> None:
        self.info_messages.append(message)

    def success(self, message: str) -> None:
        self.success_messages.append(message)

    def warning(self, message: str) -> None:
        self.warning_messages.append(message)

    def error(self, message: str) -> None:
        self.error_messages.append(message)

    def markdown(self, message: str, **kwargs: object) -> None:
        self.markdown_calls.append((message, kwargs))

    def header(self, message: str) -> None:
        self.header_calls.append(message)

    def subheader(self, message: str) -> None:
        self.subheader_calls.append(message)

    def expander(self, label: str):
        return _SimpleContext(self)

    def code(self, text: str, **kwargs: object) -> None:
        self.code_calls.append((text, kwargs))

    def empty(self) -> _Placeholder:
        placeholder = _Placeholder()
        self.empty_placeholders.append(placeholder)
        return placeholder

    def progress(self, value: float) -> _ProgressBar:
        bar = _ProgressBar(value)
        self.progress_bars.append(bar)
        return bar

    def container(self):
        container = _Container()
        self.container_entries.append(container)
        return _ContainerContext(container)

    # Input widgets
    def selectbox(
        self, message: str, options: list[str], index: int = 0, key: str | None = None
    ):
        choice = options[index if 0 <= index < len(options) else 0]
        if key is not None:
            self.selectbox_values[key] = choice
        return choice

    def text_input(self, message: str, value: str = "", key: str | None = None):
        if key is not None:
            self.text_inputs[key] = value
        return value

    def checkbox(self, message: str, value: bool = False, key: str | None = None):
        if key is not None:
            self.checkbox_values[key] = value
        return value

    # Compatibility helpers
    def __getattr__(self, name: str):  # pragma: no cover - defensive
        raise AttributeError(name)


class _SimpleContext:
    def __init__(self, streamlit: FakeStreamlit) -> None:
        self._streamlit = streamlit

    def __enter__(self) -> FakeStreamlit:
        return self._streamlit

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - context exit
        return None


class _Placeholder:
    def __init__(self) -> None:
        self.markdown_calls: list[str] = []
        self.info_calls: list[str] = []
        self.empty_calls = 0

    def markdown(self, content: str) -> None:
        self.markdown_calls.append(content)

    def info(self, content: str) -> None:
        self.info_calls.append(content)

    def empty(self) -> None:
        self.empty_calls += 1


class _ProgressBar:
    def __init__(self, initial: float) -> None:
        self.progress_calls: list[float] = [initial]

    def progress(self, value: float) -> None:
        self.progress_calls.append(value)


class _Container:
    def __init__(self) -> None:
        self.markdown_calls: list[str] = []
        self.success_calls: list[str] = []
        self.progress_bars: list[_ProgressBar] = []

    def markdown(self, content: str) -> None:
        self.markdown_calls.append(content)

    def progress(self, value: float) -> _ProgressBar:
        bar = _ProgressBar(value)
        self.progress_bars.append(bar)
        return bar

    def success(self, content: str) -> None:
        self.success_calls.append(content)


class _ContainerContext:
    def __init__(self, container: _Container) -> None:
        self._container = container

    def __enter__(self) -> _Container:
        return self._container

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - context exit
        return None


def exercise_webui_bridge() -> None:
    fake_streamlit = FakeStreamlit()
    sys.modules["streamlit"] = fake_streamlit

    import devsynth.interface.webui_bridge as bridge

    module = bridge if COVERAGE_MODE else importlib.reload(bridge)
    module.st = fake_streamlit

    indicator = module.WebUIProgressIndicator("Root", 8)
    indicator.update(description="phase", status="running")
    subtask = indicator.add_subtask("child", total=4)
    indicator.update_subtask(subtask, advance=2, description="child-step")
    nested = indicator.add_nested_subtask(subtask, "nested", total=2, status=None)
    indicator.update_nested_subtask(subtask, nested, advance=1)
    indicator.complete_nested_subtask(subtask, nested)
    indicator.complete_subtask(subtask)
    indicator.complete()

    ui = module.WebUIBridge()
    ui.ask_question("Question?", default="answer")
    ui.confirm_choice("Continue?", default=True)

    fake_streamlit.info_messages.clear()
    fake_streamlit.success_messages.clear()
    fake_streamlit.warning_messages.clear()
    fake_streamlit.error_messages.clear()

    ui.display_result("info", message_type="info")
    ui.display_result("success", message_type="success")
    ui.display_result("warn", message_type="warning")
    ui.display_result("err", message_type="error")
    ui.display_result("highlight", highlight=True)
    ui.display_result("plain")

    ui.create_progress("Task", total=5)

    fake_streamlit.session_state = SimpleNamespace()
    manager = ui.get_wizard_manager("wiz", steps=2, initial_state={"step": 0})
    wizard_state = manager.get_wizard_state()
    wizard_state.set("step", 1)
    ui.get_wizard_state("wiz", steps=2)
    namespace = SimpleNamespace()
    module.WebUIBridge.get_session_value(namespace, "missing", default=None)
    module.WebUIBridge.set_session_value(namespace, "key", "value")


def exercise_webui_module() -> None:
    fake_streamlit = FakeStreamlit()
    sys.modules["streamlit"] = fake_streamlit

    import devsynth.interface.webui as webui

    module = webui if COVERAGE_MODE else importlib.reload(webui)
    module._STREAMLIT = fake_streamlit
    module.st = fake_streamlit  # type: ignore[assignment]

    ui = module.WebUI()
    fake_streamlit.session_state.screen_width = 500
    ui.get_layout_config()
    fake_streamlit.session_state.screen_width = 800
    ui.get_layout_config()
    fake_streamlit.session_state.screen_width = 1200
    ui.get_layout_config()

    ui.ask_question("Choice?", choices=["a", "b"], default="b")
    ui.ask_question("Input?", default="text")
    ui.confirm_choice("Confirm?", default=True)

    ui.display_result("[bold]Alert[/bold] message")
    ui.display_result("WARNING: caution")
    ui.display_result("ERROR: failure")
    ui.display_result("Success", message_type="success")
    ui.display_result("Highlight", highlight=True)
    ui.display_result("ERROR: File not found: config.yaml")
    ui.display_result("SUCCESS: completed successfully")
    ui.display_result("# Welcome")
    ui.display_result("## Section heading")
    ui.display_result("### Minor heading")

    ui._render_traceback("Traceback (most recent call last):\n...")
    ui._format_error_message(ValueError("boom"))

    sample_errors = {
        "File not found error": "file_not_found",
        "Permission denied": "permission_denied",
        "Invalid parameter": "invalid_parameter",
        "Invalid format": "invalid_format",
        "Missing key": "key_error",
        "Type error": "type_error",
        "Configuration error": "config_error",
        "Connection error": "connection_error",
        "API error": "api_error",
        "Validation error": "validation_error",
        "Syntax error": "syntax_error",
        "Import error": "import_error",
    }
    for message, expected in sample_errors.items():
        error_type = ui._get_error_type(message)
        if error_type == expected:
            ui._get_error_suggestions(error_type)
            ui._get_documentation_links(error_type)

    progress = module.WebUI._UIProgress("Script Task", 4)
    progress.update(advance=1, description="phase-one")
    subtask_id = progress.add_subtask("script-sub", total=2)
    progress.update_subtask(subtask_id, advance=1, description="halfway")

    if hasattr(progress, "add_nested_subtask"):
        nested_id = progress.add_nested_subtask(
            subtask_id, "nested", total=2, status=None
        )
        progress.update_nested_subtask(subtask_id, nested_id, advance=1)
        progress.complete_nested_subtask(subtask_id, nested_id)

    progress.complete_subtask(subtask_id)
    progress.complete()


if __name__ == "__main__":
    exercise_webui_bridge()
    exercise_webui_module()
