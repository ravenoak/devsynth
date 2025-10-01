"""Streamlit WebUI implementation for DevSynth."""

from __future__ import annotations

import importlib
import time
from collections.abc import Sequence
from pathlib import Path as _ModulePath
from types import ModuleType
from typing import Any
from unittest.mock import MagicMock

from devsynth.exceptions import DevSynthError
from devsynth.interface.ux_bridge import ProgressIndicator, UXBridge, sanitize_output
from devsynth.logging_setup import DevSynthLogger

__path__ = [str(_ModulePath(__file__).with_suffix(""))]
if __spec__ is not None:  # pragma: no cover - import system detail
    __spec__.submodule_search_locations = __path__

del _ModulePath

webui_commands = importlib.import_module(f"{__name__}.commands")
_rendering = importlib.import_module(f"{__name__}.rendering")
PageRenderer = _rendering.PageRenderer
_routing = importlib.import_module(f"{__name__}.routing")
Router = _routing.Router
del _rendering, _routing

_STREAMLIT: ModuleType | None = None


def _require_streamlit() -> ModuleType:
    global _STREAMLIT
    if _STREAMLIT is None:
        try:  # pragma: no cover - optional dependency handling
            _STREAMLIT = importlib.import_module("streamlit")
        except Exception as exc:  # pragma: no cover - provide guidance
            raise DevSynthError(
                "Streamlit is required to use the DevSynth WebUI. "
                "Install the optional extra:\n"
                "  poetry install --with dev --extras webui"
            ) from exc
    return _STREAMLIT


class _LazyStreamlit:
    def __getattr__(self, name: str) -> Any:  # type: ignore[override]
        module = _require_streamlit()
        return getattr(module, name)


st = _LazyStreamlit()  # type: ignore[misc]

for _name in webui_commands.__all__:
    globals()[_name] = getattr(webui_commands, _name)

del _name


logger = DevSynthLogger(__name__)


class WebUI(PageRenderer, UXBridge):
    """Streamlit façade that wires rendering, routing, and command helpers."""

    def __init__(self) -> None:
        super().__init__()
        self._router: Router | None = None

    @property
    def streamlit(self):  # type: ignore[override]
        return st

    def get_layout_config(self) -> dict[str, Any]:
        st = self.streamlit
        session_state = getattr(st, "session_state", None)
        screen_width = (
            getattr(session_state, "screen_width", 1200) if session_state else 1200
        )

        if screen_width < 768:
            return {
                "columns": 1,
                "sidebar_width": "100%",
                "content_width": "100%",
                "font_size": "small",
                "padding": "0.5rem",
                "is_mobile": True,
            }
        if screen_width < 992:
            return {
                "columns": 2,
                "sidebar_width": "30%",
                "content_width": "70%",
                "font_size": "medium",
                "padding": "1rem",
                "is_mobile": False,
            }
        return {
            "columns": 3,
            "sidebar_width": "20%",
            "content_width": "80%",
            "font_size": "medium",
            "padding": "1.5rem",
            "is_mobile": False,
        }

    def ask_question(
        self,
        message: str,
        *,
        choices: Sequence[str] | None = None,
        default: str | None = None,
        show_default: bool = True,
    ) -> str:
        st = self.streamlit
        if choices:
            index = 0
            if default in choices:
                index = list(choices).index(default)
            return st.selectbox(message, list(choices), index=index, key=message)
        return st.text_input(message, value=default or "", key=message)

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        st = self.streamlit
        return st.checkbox(message, value=default, key=message)

    def display_result(
        self, message: str, *, highlight: bool = False, message_type: str | None = None
    ) -> None:
        st = self.streamlit
        message = sanitize_output(message)

        if "[" in message and "]" in message:
            message = (
                message.replace("[bold]", "**")
                .replace("[/bold]", "**")
                .replace("[italic]", "*")
                .replace("[/italic]", "*")
                .replace("[green]", '<span style="color:green">')
                .replace("[/green]", "</span>")
                .replace("[red]", '<span style="color:red">')
                .replace("[/red]", "</span>")
                .replace("[blue]", '<span style="color:blue">')
                .replace("[/blue]", "</span>")
                .replace("[yellow]", '<span style="color:orange">')
                .replace("[/yellow]", "</span>")
                .replace("[cyan]", '<span style="color:cyan">')
                .replace("[/cyan]", "</span>")
            )
            markdown_fn = getattr(st, "markdown", st.write)
            markdown_fn(message, unsafe_allow_html=True)
            return

        if message_type:
            if message_type == "error":
                st.error(message)
                error_type = self._get_error_type(message)
                if error_type:
                    suggestions = self._get_error_suggestions(error_type)
                    if suggestions:
                        st.markdown("**Suggestions:**")
                        for suggestion in suggestions:
                            st.markdown(f"- {suggestion}")
                    doc_links = self._get_documentation_links(error_type)
                    if doc_links:
                        st.markdown("**Documentation:**")
                        for title, url in doc_links.items():
                            st.markdown(f"- [{title}]({url})")
            elif message_type == "warning":
                st.warning(message)
            elif message_type == "success":
                st.success(message)
            elif message_type == "info":
                getattr(st, "info", st.write)(message)
            else:
                st.write(message)
            return

        if highlight:
            getattr(st, "info", st.write)(message)
            return
        if message.startswith("ERROR") or message.startswith("FAILED"):
            st.error(message)
            error_type = self._get_error_type(message)
            if error_type:
                suggestions = self._get_error_suggestions(error_type)
                if suggestions:
                    st.markdown("**Suggestions:**")
                    for suggestion in suggestions:
                        st.markdown(f"- {suggestion}")
                doc_links = self._get_documentation_links(error_type)
                if doc_links:
                    st.markdown("**Documentation:**")
                    for title, url in doc_links.items():
                        st.markdown(f"- [{title}]({url})")
            return
        if message.startswith("WARNING"):
            st.warning(message)
            return
        if message.startswith("SUCCESS") or "successfully" in message.lower():
            st.success(message)
            return
        if message.startswith("#"):
            level = len(message.split(" ")[0])
            if level == 1:
                st.header(message[2:])
            elif level == 2:
                st.subheader(message[3:])
            else:
                st.markdown(f"**{message[level+1:]}**")
            return
        st.write(message)

    def _render_traceback(self, traceback_text: str) -> None:
        st = self.streamlit
        with st.expander("Technical Details (for debugging)"):
            st.code(traceback_text, language="python")

    def _format_error_message(self, error: Exception) -> str:
        return f"{error.__class__.__name__}: {error}".strip()

    def _get_error_type(self, message: str) -> str:
        if "File not found" in message:
            return "file_not_found"
        if "Permission denied" in message:
            return "permission_denied"
        if "Invalid parameter" in message:
            return "invalid_parameter"
        if "Invalid format" in message:
            return "invalid_format"
        if "Missing key" in message or "KeyError" in message:
            return "key_error"
        if "Type error" in message or "TypeError" in message:
            return "type_error"
        if "Configuration error" in message:
            return "config_error"
        if "Connection error" in message:
            return "connection_error"
        if "API error" in message:
            return "api_error"
        if "Validation error" in message:
            return "validation_error"
        if "Syntax error" in message:
            return "syntax_error"
        if "Import error" in message:
            return "import_error"
        return ""

    def _get_error_suggestions(self, error_type: str) -> list[str]:
        suggestions = {
            "file_not_found": [
                "Check that the file path is correct",
                "Verify that the file exists in the specified location",
                "If using a relative path, make sure you're in the correct directory",
            ],
            "permission_denied": [
                "Check that you have the necessary permissions to access the file",
                "Try running the command with elevated privileges",
                "Verify that the file is not locked by another process",
            ],
            "invalid_parameter": [
                "Check the command syntax and parameters",
                "Refer to the documentation for the correct parameter format",
                "Use the --help flag to see available options",
            ],
            "invalid_format": [
                "Check that the file format is supported",
                "Verify that the file content matches the expected format",
                "Try using a different format option if available",
            ],
            "key_error": [
                "Ensure the specified key exists in the data structure",
                "Check for typos in configuration keys",
            ],
            "type_error": [
                "Verify that values match the expected types",
                "Convert inputs to the correct type before passing them",
            ],
            "config_error": [
                "Check your configuration file for errors",
                "Verify that all required configuration options are set",
                "Try resetting to default configuration with 'devsynth config --reset'",
            ],
            "connection_error": [
                "Check your internet connection",
                "Verify that the service you're trying to connect to is available",
                "Check if a firewall is blocking the connection",
            ],
            "api_error": [
                "Verify that your API key is valid",
                "Check that you have sufficient quota for the API",
                "Verify that the API endpoint is correct",
            ],
            "validation_error": [
                "Check that your input meets all validation requirements",
                "Verify that all required fields are provided",
                "Check for formatting errors in your input",
            ],
            "syntax_error": [
                "Check for syntax errors in your code or input",
                "Verify that all brackets, quotes, and parentheses are properly closed",
                "Check for typos or missing characters",
            ],
            "import_error": [
                "Verify that the required package is installed",
                "Check that the package name is spelled correctly",
                "Try reinstalling the package",
            ],
        }

        return suggestions.get(error_type, [])

    def _get_documentation_links(self, error_type: str) -> dict[str, str]:
        base_url = "https://devsynth.readthedocs.io/en/latest"
        links = {
            "file_not_found": {
                "File Handling Guide": f"{base_url}/user_guides/file_handling.html",
                "Common File Errors": (
                    f"{base_url}/user_guides/troubleshooting.html#file-errors"
                ),
            },
            "permission_denied": {
                "Permission Issues": (
                    f"{base_url}/user_guides/troubleshooting.html#permission-issues"
                ),
                "Security Configuration": (
                    f"{base_url}/user_guides/security_config.html"
                ),
            },
            "invalid_parameter": {
                "Command Reference": f"{base_url}/user_guides/cli_reference.html",
                "Parameter Syntax": f"{base_url}/user_guides/command_syntax.html",
            },
            "invalid_format": {
                "Supported Formats": f"{base_url}/user_guides/file_formats.html",
                "Format Conversion": f"{base_url}/user_guides/format_conversion.html",
            },
            "key_error": {
                "Configuration Keys": (
                    f"{base_url}/user_guides/configuration.html#available-keys"
                ),
            },
            "type_error": {
                "Type Hints": f"{base_url}/developer_guides/type_hints.html",
            },
            "config_error": {
                "Configuration Guide": f"{base_url}/user_guides/configuration.html",
                "Configuration Troubleshooting": (
                    f"{base_url}/user_guides/troubleshooting.html#configuration-issues"
                ),
            },
            "connection_error": {
                "Network Configuration": f"{base_url}/user_guides/network_config.html",
                "Connection Troubleshooting": (
                    f"{base_url}/user_guides/troubleshooting.html#connection-issues"
                ),
            },
            "api_error": {
                "API Integration Guide": f"{base_url}/user_guides/api_integration.html",
                "API Troubleshooting": (
                    f"{base_url}/user_guides/troubleshooting.html#api-issues"
                ),
            },
            "validation_error": {
                "Input Validation": f"{base_url}/user_guides/input_validation.html",
                "Validation Rules": f"{base_url}/user_guides/validation_rules.html",
            },
            "syntax_error": {
                "Syntax Guide": f"{base_url}/user_guides/syntax_guide.html",
                "Common Syntax Errors": (
                    f"{base_url}/user_guides/troubleshooting.html#syntax-issues"
                ),
            },
            "import_error": {
                "Package Management": f"{base_url}/user_guides/package_management.html",
                "Import Troubleshooting": (
                    f"{base_url}/user_guides/troubleshooting.html#import-issues"
                ),
            },
        }

        return links.get(error_type, {})

    class _UIProgress(ProgressIndicator):
        def __init__(self, description: str, total: int) -> None:
            st = globals()["st"]
            self._description = description
            self._total = total
            self._current = 0
            self._status = "Starting..."
            self._subtasks: dict[str, dict[str, Any]] = {}
            empty_fn = getattr(st, "empty", lambda: MagicMock())
            progress_fn = getattr(st, "progress", lambda *_, **__: MagicMock())
            self._status_container = empty_fn()
            self._bar_container = progress_fn(0.0)
            self._time_container = empty_fn()
            self._subtask_containers: dict[str, dict[str, Any]] = {}
            self._start_time = time.time()
            self._update_times: list[tuple[float, float]] = []
            self._streamlit = st
            self._update_display()

        def _update_display(self) -> None:
            progress_pct = min(1.0, self._current / self._total)
            current_time = time.time()
            self._update_times.append((current_time, self._current))

            eta_text = ""
            if self._current > 0 and progress_pct < 1.0:
                recent_updates = (
                    self._update_times[-5:]
                    if len(self._update_times) > 5
                    else self._update_times
                )
                if len(recent_updates) > 1:
                    first_time, first_progress = recent_updates[0]
                    last_time, last_progress = recent_updates[-1]
                    time_diff = last_time - first_time
                    progress_diff = last_progress - first_progress

                    if time_diff > 0 and progress_diff > 0:
                        rate = progress_diff / time_diff
                        remaining_progress = self._total - self._current
                        eta_seconds = remaining_progress / rate
                        if eta_seconds < 60:
                            eta_text = f"ETA: {int(eta_seconds)} seconds"
                        elif eta_seconds < 3600:
                            eta_text = f"ETA: {int(eta_seconds / 60)} minutes"
                        else:
                            eta_text = (
                                f"ETA: {int(eta_seconds / 3600)} hours, "
                                f"{int((eta_seconds % 3600) / 60)} minutes"
                            )

            status_text = f"**{self._description}** - {int(progress_pct * 100)}%"
            self._status_container.markdown(status_text)
            logger.debug(
                "Progress update for '%s': %s/%s status=%s",
                self._description,
                self._current,
                self._total,
                self._status,
            )

            if eta_text:
                self._time_container.info(eta_text)
            else:
                self._time_container.empty()

            self._bar_container.progress(progress_pct)

        def update(
            self,
            *,
            advance: float = 1,
            description: str | None = None,
            status: str | None = None,
        ) -> None:
            self._current += advance
            if description:
                self._description = sanitize_output(description)

            if status is not None:
                self._status = sanitize_output(status)
            else:
                if self._current >= self._total:
                    self._status = "Complete"
                elif self._current >= 0.99 * self._total:
                    self._status = "Finalizing..."
                elif self._current >= 0.75 * self._total:
                    self._status = "Almost done..."
                elif self._current >= 0.5 * self._total:
                    self._status = "Halfway there..."
                elif self._current >= 0.25 * self._total:
                    self._status = "Processing..."
                else:
                    self._status = "Starting..."

            self._update_display()

        def complete(self) -> None:
            self._current = self._total
            self._status = "Complete"
            self._update_display()
            for subtask_id in list(self._subtasks):
                self.complete_subtask(subtask_id)
            getattr(self._streamlit, "success", self._streamlit.write)(
                f"Completed: {self._description}"
            )

        def add_subtask(
            self,
            description: str,
            total: int = 100,
            status: str = "Starting...",
        ) -> str:
            st = self._streamlit
            task_id = f"subtask_{len(self._subtasks)}"
            self._subtasks[task_id] = {
                "description": sanitize_output(description),
                "total": total,
                "current": 0,
                "status": sanitize_output(status),
            }
            with st.container() as container:
                progress_bar = container.progress(0.0)
            self._subtask_containers[task_id] = {
                "container": container,
                "bar": progress_bar,
            }
            self._update_subtask_display(task_id)
            return task_id

        def _update_subtask_display(self, task_id: str) -> None:
            if task_id not in self._subtasks or task_id not in self._subtask_containers:
                return
            subtask = self._subtasks[task_id]
            containers = self._subtask_containers[task_id]
            progress_pct = min(1.0, subtask["current"] / subtask["total"])
            status_suffix = subtask.get("status", "")
            status_text = (
                f"&nbsp;&nbsp;&nbsp;&nbsp;**{subtask['description']}** - "
                f"{int(progress_pct * 100)}%"
            )
            if status_suffix:
                status_text = f"{status_text} ({status_suffix})"
            containers["container"].markdown(status_text)
            containers["bar"].progress(progress_pct)

        def update_subtask(
            self,
            task_id: str,
            advance: float = 1,
            description: str | None = None,
            status: str | None = None,
        ) -> None:
            if task_id not in self._subtasks:
                return
            self._subtasks[task_id]["current"] += advance
            if description:
                self._subtasks[task_id]["description"] = sanitize_output(description)
            if status is not None:
                self._subtasks[task_id]["status"] = sanitize_output(status)
            self._update_subtask_display(task_id)

        def complete_subtask(self, task_id: str) -> None:
            if task_id not in self._subtasks:
                return
            self._subtasks[task_id]["current"] = self._subtasks[task_id]["total"]
            self._subtasks[task_id]["status"] = "Complete"
            self._update_subtask_display(task_id)
            subtask = self._subtasks[task_id]
            containers = self._subtask_containers.get(task_id)
            if containers:
                containers["container"].success(f"Completed: {subtask['description']}")

    def create_progress(
        self, description: str, *, total: int = 100
    ) -> ProgressIndicator:
        return self._UIProgress(sanitize_output(description), total)

    def _ensure_router(self) -> Router:
        if self._router is None:
            self._router = Router(self, self.navigation_items())
        return self._router

    def run(self) -> None:
        st = self.streamlit
        try:
            st.set_page_config(page_title="DevSynth WebUI", layout="wide")
        except Exception as exc:  # noqa: BLE001
            self.display_result(f"ERROR: {exc}")
            return

        js_code = """
        <script>
        function updateScreenWidth() {
            const width = window.innerWidth;
            const data = {
                width: width,
                height: window.innerHeight
            };
            if (window.parent.streamlit) {
                window.parent.streamlit.setComponentValue(data);
            }
        }
        updateScreenWidth();
        window.addEventListener('resize', updateScreenWidth);
        </script>
        """
        components = getattr(st, "components", None)
        html_fn = None
        if components and hasattr(components, "v1"):
            html_fn = getattr(components.v1, "html", None)
        if callable(html_fn):
            try:
                html_fn(js_code, height=0)
            except Exception as exc:  # noqa: BLE001
                self.display_result(f"ERROR: {exc}")
                return

        session_state = getattr(st, "session_state", None)
        if session_state is not None and "screen_width" not in session_state:
            session_state.screen_width = 1200
            session_state.screen_height = 800

        layout_config = self.get_layout_config()
        custom_css = f"""
        <style>
            .main .block-container {{
                padding: {layout_config["padding"]};
            }}
            .stSidebar .sidebar-content {{
                width: {layout_config["sidebar_width"]};
            }}
            .main {{
                font-size: {layout_config["font_size"]};
            }}
            .stForm {{
                background-color: #f8f9fa;
                padding: 1rem;
                border-radius: 5px;
                margin-bottom: 1rem;
            }}
            .stButton>button {{
                background-color: #4A90E2;
                color: white;
                border-radius: 4px;
                border: none;
                padding: 0.5rem 1rem;
            }}
            .stButton>button:hover {{
                background-color: #3A80D2;
            }}
        </style>
        """
        markdown_fn = getattr(st, "markdown", lambda *a, **k: None)
        markdown_fn(custom_css, unsafe_allow_html=True)

        if getattr(st.sidebar, "title", None):
            st.sidebar.title("DevSynth")
        if getattr(st.sidebar, "markdown", None):
            st.sidebar.markdown(
                (
                    '<div class="devsynth-secondary" style="font-size: 0.8rem; '
                    'margin-bottom: 2rem;">Intelligent Software Development</div>'
                ),
                unsafe_allow_html=True,
            )

        self._ensure_router().run()


def run() -> None:
    WebUI().run()


run_webui = run


__all__ = ["WebUI", "run"]
