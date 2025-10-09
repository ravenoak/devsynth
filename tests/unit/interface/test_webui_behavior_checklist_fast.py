"""Fast WebUI tests derived from the coverage behavior checklist.

Test plan anchors:

* issues/coverage-below-threshold.md §`src/devsynth/interface/webui.py`
  defines the lazy loader, prompt parity, error routing, progress lifecycle,
  and router wiring behaviors that remain uncovered.
* docs/specifications/webui-integration.md confirms rendering requirements
  for dialogs, error funnels, progress telemetry, and responsive layouts.
* docs/implementation/webui_invariants.md tracks state invariants exercised by
  the CLI/WebUI parity scenarios.

The resulting fast suite exercises the highest-value Streamlit-free branches:

* Lazy loading: `_require_streamlit` and `_LazyStreamlit` cache handling and
  installation guidance (behavior checklist §"_require_streamlit").
* Dialog prompts: `ask_question` and `confirm_choice` keep CLI/WebUI parity for
  default selections (behavior checklist §"ask_question / confirm_choice").
* Error rendering: `display_result` routes sanitized content, actionable hints,
  and markdown conversion per the WebUI integration spec.
* Progress orchestration: `_UIProgress` mirrors CLI telemetry with ETA
  estimation and sanitized subtasks.
* Router wiring and resize flows: `get_layout_config` breakpoints plus
  `run()`'s session defaults and JS resize hook.

Socratic assertions document the invariant being validated so failures surface
clear question/answer pairs for the checklist.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from itertools import count
from types import SimpleNamespace
from typing import Any, Callable, Sequence

import pytest

from devsynth.exceptions import DevSynthError
from devsynth.interface import webui, webui_bridge
from devsynth.interface.output_formatter import OutputFormatter as _OutputFormatter

pytestmark = [pytest.mark.fast]

if not hasattr(webui_bridge, "OutputFormatter"):
    webui_bridge.OutputFormatter = _OutputFormatter  # type: ignore[attr-defined]


def socratic_assert(*, condition: bool, question: str, expected: str) -> None:
    """Fail with an explicit Socratic prompt when an invariant breaks."""

    assert condition, f"Socratic check: {question}? Expected {expected}."


@dataclass
class ProgressBarRecorder:
    """Capture values written to a Streamlit progress bar."""

    values: list[float] = field(default_factory=list)

    def progress(self, value: float) -> None:
        self.values.append(value)


@dataclass
class ContainerRecorder:
    """Record container interactions for status and subtask updates."""

    owner: "BehaviorStreamlitStub"
    label: str
    markdown_calls: list[str] = field(default_factory=list)
    info_calls: list[str] = field(default_factory=list)
    empty_count: int = 0
    success_calls: list[str] = field(default_factory=list)
    progress_bars: list[ProgressBarRecorder] = field(default_factory=list)

    def markdown(self, text: str, **kwargs: Any) -> None:
        self.markdown_calls.append(text)
        self.owner.calls.append((f"{self.label}.markdown", (text,), kwargs))

    def info(self, text: str, **kwargs: Any) -> None:
        self.info_calls.append(text)
        self.owner.calls.append((f"{self.label}.info", (text,), kwargs))

    def empty(self) -> None:
        self.empty_count += 1
        self.owner.calls.append((f"{self.label}.empty", (), {}))

    def success(self, text: str, **kwargs: Any) -> None:
        self.success_calls.append(text)
        self.owner.calls.append((f"{self.label}.success", (text,), kwargs))

    def progress(self, value: float) -> ProgressBarRecorder:
        bar = ProgressBarRecorder(values=[value])
        self.progress_bars.append(bar)
        self.owner.progress_bars.append(bar)
        self.owner.calls.append((f"{self.label}.progress", (value,), {}))
        return bar

    def __enter__(self) -> "ContainerRecorder":
        self.owner.calls.append((f"{self.label}.__enter__", (), {}))
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        self.owner.calls.append((f"{self.label}.__exit__", (exc_type, exc, tb), {}))
        return None


@dataclass
class SidebarRecorder:
    """Track sidebar title, markdown, and radio interactions."""

    owner: "BehaviorStreamlitStub"
    title_calls: list[str] = field(default_factory=list)
    markdown_calls: list[str] = field(default_factory=list)
    radio_calls: list[tuple[str, tuple[str, ...], int]] = field(default_factory=list)

    def title(self, text: str) -> None:
        self.title_calls.append(text)
        self.owner.calls.append(("sidebar.title", (text,), {}))

    def markdown(self, text: str, **kwargs: Any) -> None:
        self.markdown_calls.append(text)
        self.owner.calls.append(("sidebar.markdown", (text,), kwargs))

    def radio(self, label: str, options: Sequence[str], index: int = 0) -> str:
        options_tuple = tuple(options)
        self.radio_calls.append((label, options_tuple, index))
        self.owner.calls.append(("sidebar.radio", (label, options_tuple, index), {}))
        if self.owner.radio_selection is not None:
            return self.owner.radio_selection
        return options_tuple[index]


@dataclass
class ExpanderRecorder:
    """Track usage of expanders when rendering tracebacks."""

    owner: "BehaviorStreamlitStub"
    label: str
    code_calls: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def code(self, text: str, **kwargs: Any) -> None:
        self.code_calls.append((text, kwargs))
        self.owner.calls.append((f"{self.label}.code", (text,), kwargs))

    def __enter__(self) -> "ExpanderRecorder":
        self.owner.calls.append((f"{self.label}.__enter__", (), {}))
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        self.owner.calls.append((f"{self.label}.__exit__", (exc_type, exc, tb), {}))
        return None


class SessionStateRecorder(SimpleNamespace):
    """Simple namespace that also supports membership tests."""

    def __contains__(self, key: object) -> bool:
        return hasattr(self, str(key))


class BehaviorStreamlitStub:
    """Purpose-built Streamlit surrogate for fast WebUI coverage."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []
        self.selectbox_calls: list[tuple[str, tuple[str, ...], int, str | None]] = []
        self.text_input_calls: list[tuple[str, str, str | None]] = []
        self.checkbox_calls: list[tuple[str, bool, str | None]] = []
        self.markdown_calls: list[str] = []
        self.write_calls: list[str] = []
        self.error_calls: list[str] = []
        self.warning_calls: list[str] = []
        self.success_calls: list[str] = []
        self.info_calls: list[str] = []
        self.header_calls: list[str] = []
        self.subheader_calls: list[str] = []
        self.empty_containers: list[ContainerRecorder] = []
        self.containers: list[ContainerRecorder] = []
        self.progress_bars: list[ProgressBarRecorder] = []
        self.expanders: list[ExpanderRecorder] = []
        self.html_calls: list[tuple[str, dict[str, Any]]] = []
        self.code_calls: list[tuple[str, dict[str, Any]]] = []
        self.session_state = SessionStateRecorder()
        self.sidebar = SidebarRecorder(self)
        self.components = SimpleNamespace(v1=SimpleNamespace(html=self._record_html))
        self.text_input_responses: dict[str, str] = {}
        self.checkbox_responses: dict[str, bool] = {}
        self.radio_selection: str | None = None
        self.page_config_error: Exception | None = None

    def _record_html(self, html: str, **kwargs: Any) -> None:
        self.html_calls.append((html, kwargs))
        self.calls.append(("components.v1.html", (html,), kwargs))

    def set_page_config(self, *args: Any, **kwargs: Any) -> None:
        if self.page_config_error is not None:
            raise self.page_config_error
        self.calls.append(("set_page_config", args, kwargs))

    def markdown(self, text: str, **kwargs: Any) -> None:
        self.markdown_calls.append(text)
        self.calls.append(("markdown", (text,), kwargs))

    def write(self, text: str, **kwargs: Any) -> None:
        self.write_calls.append(text)
        self.calls.append(("write", (text,), kwargs))

    def error(self, text: str, **kwargs: Any) -> None:
        self.error_calls.append(text)
        self.calls.append(("error", (text,), kwargs))

    def warning(self, text: str, **kwargs: Any) -> None:
        self.warning_calls.append(text)
        self.calls.append(("warning", (text,), kwargs))

    def success(self, text: str, **kwargs: Any) -> None:
        self.success_calls.append(text)
        self.calls.append(("success", (text,), kwargs))

    def info(self, text: str, **kwargs: Any) -> None:
        self.info_calls.append(text)
        self.calls.append(("info", (text,), kwargs))

    def code(self, text: str, **kwargs: Any) -> None:
        self.code_calls.append((text, kwargs))
        self.calls.append(("code", (text,), kwargs))

    def header(self, text: str, **kwargs: Any) -> None:
        self.header_calls.append(text)
        self.calls.append(("header", (text,), kwargs))

    def subheader(self, text: str, **kwargs: Any) -> None:
        self.subheader_calls.append(text)
        self.calls.append(("subheader", (text,), kwargs))

    def selectbox(
        self,
        label: str,
        options: Sequence[str],
        *,
        index: int = 0,
        key: str | None = None,
    ) -> str:
        options_tuple = tuple(options)
        self.selectbox_calls.append((label, options_tuple, index, key))
        self.calls.append(("selectbox", (label, options_tuple, index), {"key": key}))
        return options_tuple[index]

    def text_input(self, label: str, *, value: str = "", key: str | None = None) -> str:
        self.text_input_calls.append((label, value, key))
        self.calls.append(("text_input", (label,), {"value": value, "key": key}))
        return self.text_input_responses.get(key or label, value)

    def checkbox(
        self, label: str, *, value: bool = False, key: str | None = None
    ) -> bool:
        self.checkbox_calls.append((label, value, key))
        self.calls.append(("checkbox", (label,), {"value": value, "key": key}))
        return self.checkbox_responses.get(key or label, value)

    def empty(self) -> ContainerRecorder:
        label = f"empty[{len(self.empty_containers)}]"
        container = ContainerRecorder(self, label)
        self.empty_containers.append(container)
        self.calls.append(("empty", (), {}))
        return container

    def progress(self, value: float) -> ProgressBarRecorder:
        bar = ProgressBarRecorder(values=[value])
        self.progress_bars.append(bar)
        self.calls.append(("progress", (value,), {}))
        return bar

    def container(self) -> ContainerRecorder:
        label = f"container[{len(self.containers)}]"
        container = ContainerRecorder(self, label)
        self.containers.append(container)
        self.calls.append(("container", (), {}))
        return container

    def expander(self, label: str, **kwargs: Any) -> ExpanderRecorder:
        expander = ExpanderRecorder(self, label)
        self.expanders.append(expander)
        self.calls.append(("expander", (label,), kwargs))
        return expander


def install_streamlit_stub(monkeypatch: pytest.MonkeyPatch) -> BehaviorStreamlitStub:
    """Replace the Streamlit module with a deterministic recorder."""

    stub = BehaviorStreamlitStub()
    monkeypatch.setattr(webui, "st", stub, raising=False)
    monkeypatch.setattr(webui, "_STREAMLIT", stub, raising=False)
    return stub


def test_lazy_streamlit_forwards_attributes(monkeypatch: pytest.MonkeyPatch) -> None:
    """`_LazyStreamlit` proxies attribute lookups through `_require_streamlit`."""

    calls: list[tuple[str, str | None]] = []

    class SentinelStreamlit:
        def header(self, text: str) -> str:
            calls.append(("header", text))
            return f"header::{text}"

    sentinel = SentinelStreamlit()

    def fake_require_streamlit() -> SentinelStreamlit:
        calls.append(("require", None))
        return sentinel

    monkeypatch.setattr(webui, "_STREAMLIT", None, raising=False)
    monkeypatch.setattr(webui, "_require_streamlit", fake_require_streamlit)

    result = webui.st.header("DevSynth")

    socratic_assert(
        condition=calls == [("require", None), ("header", "DevSynth")],
        question="Does the lazy Streamlit wrapper call the loader once and forward attributes",
        expected="_require_streamlit executes before delegating to the header() method",
    )
    socratic_assert(
        condition=result == "header::DevSynth",
        question="Is the delegated result returned from the original Streamlit method",
        expected="the header() return value propagates through the proxy",
    )


def test_require_streamlit_guidance_and_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lazy loader emits install guidance once and caches the module."""

    monkeypatch.setattr(webui, "_STREAMLIT", None, raising=False)
    sentinel = SimpleNamespace(name="streamlit-sentinel")
    import_attempts: list[str] = []

    def import_once(name: str) -> SimpleNamespace:
        import_attempts.append(name)
        return sentinel

    monkeypatch.setattr(webui.importlib, "import_module", import_once)
    loaded = webui._require_streamlit()
    socratic_assert(
        condition=loaded is sentinel,
        question="Does the lazy loader return the imported Streamlit module",
        expected="the cached module object",
    )
    socratic_assert(
        condition=webui._require_streamlit() is sentinel,
        question="Is the cached Streamlit module reused on subsequent calls",
        expected="reuse the cached module",
    )
    socratic_assert(
        condition=import_attempts == ["streamlit"],
        question="How many import attempts are required after caching",
        expected="a single import attempt",
    )

    monkeypatch.setattr(webui, "_STREAMLIT", None, raising=False)

    def import_fail(name: str) -> None:
        raise ImportError("streamlit missing")

    monkeypatch.setattr(webui.importlib, "import_module", import_fail)
    with pytest.raises(DevSynthError) as excinfo:
        webui._require_streamlit()
    socratic_assert(
        condition="poetry install --with dev --extras webui" in str(excinfo.value),
        question="Does the lazy loader guide installation when Streamlit is absent",
        expected="error message includes poetry install guidance",
    )


def test_ask_question_and_confirm_choice_respects_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Select boxes and checkboxes mirror CLI defaults without Streamlit."""

    stub = install_streamlit_stub(monkeypatch)
    ui = webui.WebUI()

    selection = ui.ask_question(
        "Interface",
        choices=("CLI", "WebUI"),
        default="WebUI",
    )
    socratic_assert(
        condition=selection == "WebUI",
        question="Does ask_question return the CLI's default option",
        expected="'WebUI'",
    )
    socratic_assert(
        condition=stub.selectbox_calls[0][2] == 1,
        question="Is the selectbox index aligned with the default choice",
        expected="index 1 for 'WebUI'",
    )

    direct_selection = webui.WebUI.ask_question(
        ui,
        "Interface (unbound)",
        choices=("CLI", "WebUI"),
        default="CLI",
    )
    socratic_assert(
        condition=direct_selection == "CLI",
        question="Does calling the unbound ask_question still honor defaults",
        expected="the CLI option is returned",
    )

    fallback = ui.ask_question(
        "Interface",
        choices=("CLI", "WebUI"),
        default="Missing",
    )
    socratic_assert(
        condition=fallback == "CLI",
        question="What happens when the default is absent from the choice list",
        expected="the first option is selected",
    )

    stub.text_input_responses["Notes"] = "typed via stub"
    captured = ui.ask_question("Notes", default="prefill")
    socratic_assert(
        condition=captured == "typed via stub",
        question="Does text_input capture the stubbed free-form entry",
        expected="the recorded override value",
    )

    stub.checkbox_responses["Proceed?"] = True
    confirmed = ui.confirm_choice("Proceed?", default=False)
    socratic_assert(
        condition=confirmed is True,
        question="Does confirm_choice honor the expected CLI default",
        expected="True",
    )
    socratic_assert(
        condition=stub.checkbox_calls[0][1] is False,
        question="Is the checkbox invoked with the CLI default before override",
        expected="the default False value",
    )

    direct_confirm = webui.WebUI.confirm_choice(ui, "Proceed? (unbound)", default=True)
    socratic_assert(
        condition=direct_confirm is True,
        question="Does the unbound confirm_choice preserve defaults",
        expected="True when default=True",
    )


def test_display_result_routes_error_and_highlight_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Error prompts, highlights, headers, and markdown obey spec routing."""

    stub = install_streamlit_stub(monkeypatch)
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
        lambda self, error_type: {"API Guide": "https://docs.invalid/api"},
    )

    ui.display_result("<b>Auth failed</b>", message_type="error")
    socratic_assert(
        condition=stub.error_calls[0] == "&lt;b&gt;Auth failed&lt;/b&gt;",
        question="Are error messages sanitized before rendering",
        expected="escaped HTML content",
    )
    socratic_assert(
        condition=stub.markdown_calls[:3]
        == ["**Suggestions:**", "- Check API token", "- Retry request"],
        question="Do actionable suggestions appear before documentation links",
        expected="a markdown bullet list",
    )
    socratic_assert(
        condition=stub.markdown_calls[3] == "**Documentation:**",
        question="Is documentation highlighted after suggestions",
        expected="a bold Documentation label",
    )
    socratic_assert(
        condition=stub.markdown_calls[4] == "- [API Guide](https://docs.invalid/api)",
        question="Are documentation links rendered as markdown bullets",
        expected="the API guide hyperlink",
    )

    ui.display_result("Reminder", highlight=True)
    socratic_assert(
        condition=stub.info_calls[-1] == "Reminder",
        question="Does highlight mode route through the info channel",
        expected="an info() call with the same text",
    )

    ui.display_result("[bold]Focus[/bold] message")
    socratic_assert(
        condition=stub.markdown_calls[-1] == "**Focus** message",
        question="Do legacy markup tags convert to Markdown",
        expected="Markdown bold syntax",
    )

    ui.display_result("# Heading One")
    ui.display_result("## Heading Two")
    ui.display_result("### Heading Three")
    socratic_assert(
        condition=stub.header_calls[-1] == "Heading One",
        question="Does a single hash route to header()",
        expected="header stripped of hash prefix",
    )
    socratic_assert(
        condition=stub.subheader_calls[-1] == "Heading Two",
        question="Does a double hash route to subheader()",
        expected="subheader stripped of prefix",
    )
    socratic_assert(
        condition=stub.markdown_calls[-1] == "**Heading Three**",
        question="Are deeper headings rendered as bold markdown",
        expected="double-asterisk wrapped heading",
    )

    ui.display_result("General update")
    socratic_assert(
        condition=stub.write_calls[-1] == "General update",
        question="Do plain messages fall back to write()",
        expected="a direct write() call",
    )


def test_display_result_handles_multiple_message_types(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Warnings, successes, info, and unknown types route to the right channels."""

    stub = install_streamlit_stub(monkeypatch)
    ui = webui.WebUI()

    ui.display_result("Be cautious", message_type="warning")
    socratic_assert(
        condition=stub.warning_calls[-1] == "Be cautious",
        question="Do warnings surface via Streamlit.warning",
        expected="warning channel invoked",
    )

    ui.display_result("All good", message_type="success")
    socratic_assert(
        condition=stub.success_calls[-1] == "All good",
        question="Are success messages routed to the success channel",
        expected="success() receives the message",
    )

    ui.display_result("FYI", message_type="info")
    socratic_assert(
        condition=stub.info_calls[-1] == "FYI",
        question="Does info routing use Streamlit.info",
        expected="info() records the text",
    )

    ui.display_result("Fallback", message_type="unexpected")
    socratic_assert(
        condition=stub.write_calls[-1] == "Fallback",
        question="How are unknown message types handled",
        expected="fallback to write()",
    )


def test_display_result_info_and_error_fallbacks_sanitize(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing Streamlit channels fall back to ``write`` with sanitized payloads."""

    monkeypatch.delattr(BehaviorStreamlitStub, "info")
    stub = install_streamlit_stub(monkeypatch)

    sanitized_inputs: list[str] = []

    def fake_sanitize(text: str) -> str:
        sanitized_inputs.append(text)
        return text.replace("<", "&lt;").replace(">", "&gt;")

    monkeypatch.setattr(webui, "sanitize_output", fake_sanitize)

    ui = webui.WebUI()
    write_before = len(stub.write_calls)
    ui.display_result("FYI <tag>", message_type="info")
    ui.display_result("ERROR: <danger>", message_type="error")
    ui.display_result("Highlight <tag>", highlight=True)

    socratic_assert(
        condition=sanitized_inputs
        == ["FYI <tag>", "ERROR: <danger>", "Highlight <tag>"],
        question="Were all fallback branches sanitized before rendering",
        expected="sanitize_output captures each message",
    )

    socratic_assert(
        condition=stub.write_calls[write_before] == "FYI &lt;tag&gt;",
        question="Does message_type='info' fall back to write() when info() is missing",
        expected="sanitized info message recorded via write()",
    )
    socratic_assert(
        condition=stub.error_calls[-1] == "ERROR: &lt;danger&gt;",
        question="Are error messages sanitized even when the error channel exists",
        expected="sanitized error captured via Streamlit.error",
    )
    socratic_assert(
        condition=stub.write_calls[write_before + 1] == "Highlight &lt;tag&gt;",
        question="Does highlight mode share the same fallback when info() is absent",
        expected="highlight text sanitized and routed to write()",
    )


def test_display_result_markup_fallback_uses_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Markdown rendering falls back to ``write`` when ``markdown`` is absent."""

    monkeypatch.delattr(BehaviorStreamlitStub, "markdown")
    stub = install_streamlit_stub(monkeypatch)

    sanitized_inputs: list[str] = []

    def fake_sanitize(text: str) -> str:
        sanitized_inputs.append(text)
        return text.replace("<", "&lt;")

    monkeypatch.setattr(webui, "sanitize_output", fake_sanitize)

    ui = webui.WebUI()
    write_before = len(stub.write_calls)
    ui.display_result("[bold]Alert[/bold] <danger>")

    socratic_assert(
        condition=sanitized_inputs == ["[bold]Alert[/bold] <danger>"],
        question="Was the markup-bearing message sanitized prior to fallback",
        expected="sanitize_output invoked once",
    )
    socratic_assert(
        condition=stub.write_calls[write_before] == "**Alert** &lt;danger>",
        question="Does the markdown branch convert tags even without st.markdown",
        expected="write() receives the Markdown-converted output",
    )


def test_display_result_error_prefix_triggers_guidance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Error prefixes emit suggestions, docs, warnings, and success markers."""

    stub = install_streamlit_stub(monkeypatch)
    ui = webui.WebUI()

    ui.display_result("ERROR: File not found when loading config")
    socratic_assert(
        condition=stub.error_calls[-1] == "ERROR: File not found when loading config",
        question="Do error-prefixed messages route through st.error",
        expected="error channel invoked",
    )
    socratic_assert(
        condition="**Suggestions:**" in stub.markdown_calls,
        question="Are remediation suggestions surfaced for file errors",
        expected="suggestions markdown present",
    )
    socratic_assert(
        condition="**Documentation:**" in stub.markdown_calls,
        question="Are documentation links provided alongside suggestions",
        expected="documentation header rendered",
    )

    ui.display_result("WARNING: Disk almost full")
    socratic_assert(
        condition=stub.warning_calls[-1] == "WARNING: Disk almost full",
        question="Does WARNING prefix map to Streamlit.warning",
        expected="warning channel invoked",
    )

    ui.display_result("SUCCESS: Upload complete")
    socratic_assert(
        condition=stub.success_calls[-1] == "SUCCESS: Upload complete",
        question="Does SUCCESS prefix reach the success channel",
        expected="success channel invoked",
    )

    ui.display_result("Operation completed successfully")
    socratic_assert(
        condition=stub.success_calls[-1] == "Operation completed successfully",
        question="Do lowercase success keywords trigger success routing",
        expected="success() handles case-insensitive cues",
    )


def test_display_result_covers_all_message_channels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sanitized conversion and every message channel execute as specified."""

    stub = install_streamlit_stub(monkeypatch)
    ui = webui.WebUI()

    ui.display_result("[red]Alert[/red] [green]Ready[/green]")
    socratic_assert(
        condition='<span style="color:red">Alert</span>' in stub.markdown_calls[-1]
        and '<span style="color:green">Ready</span>' in stub.markdown_calls[-1],
        question="Are color tags translated into HTML span markup",
        expected="red and green spans rendered in the markdown output",
    )

    markdown_index = len(stub.markdown_calls)
    ui.display_result("API error raised", message_type="error")
    recent_markdown = stub.markdown_calls[markdown_index:]
    socratic_assert(
        condition=stub.error_calls[-1] == "API error raised",
        question="Does the message_type=error branch invoke Streamlit.error",
        expected="error() receives the sanitized message",
    )
    suggestions_section = recent_markdown[1:4]
    socratic_assert(
        condition=recent_markdown[0] == "**Suggestions:**"
        and set(suggestions_section)
        == {
            "- Verify that your API key is valid",
            "- Check that you have sufficient quota for the API",
            "- Verify that the API endpoint is correct",
        },
        question="Are API remediation hints presented before documentation",
        expected="suggestions header followed by all three API tips",
    )
    doc_entries = [entry for entry in recent_markdown if entry.startswith("- [")]
    socratic_assert(
        condition="**Documentation:**" in recent_markdown
        and any(entry.startswith("- [API Integration Guide]") for entry in doc_entries),
        question="Do API documentation links follow the suggestions list",
        expected="documentation heading followed by hyperlink markdown",
    )

    ui.display_result("Take caution", message_type="warning")
    socratic_assert(
        condition=stub.warning_calls[-1] == "Take caution",
        question="Does the warning channel activate for message_type='warning'",
        expected="warning() captures the message",
    )

    ui.display_result("Job done", message_type="success")
    socratic_assert(
        condition=stub.success_calls[-1] == "Job done",
        question="Does the success branch forward to Streamlit.success",
        expected="success() records the completion text",
    )

    ui.display_result("FYI", message_type="info")
    socratic_assert(
        condition=stub.info_calls[-1] == "FYI",
        question="Is the info channel available when message_type is 'info'",
        expected="info() receives the FYI message",
    )

    ui.display_result("Unmapped", message_type="custom")
    socratic_assert(
        condition=stub.write_calls[-1] == "Unmapped",
        question="How are unknown message types handled",
        expected="fallback to write() for unmapped types",
    )

    ui.display_result("Highlight me", highlight=True)
    socratic_assert(
        condition=stub.info_calls[-1] == "Highlight me",
        question="Does highlight=True route through the info channel",
        expected="info() displays the highlighted message",
    )

    markdown_checkpoint = len(stub.markdown_calls)
    ui.display_result("ERROR: File not found in workspace")
    file_error_markdown = stub.markdown_calls[markdown_checkpoint:]
    socratic_assert(
        condition=file_error_markdown[:2]
        == ["**Suggestions:**", "- Check that the file path is correct"],
        question="Do file errors surface remediation tips",
        expected="suggestions header and bullet rendered",
    )
    socratic_assert(
        condition=file_error_markdown[2]
        == "- Verify that the file exists in the specified location",
        question="Are follow-up suggestions preserved",
        expected="second suggestion references the file location",
    )
    file_doc_entries = [
        entry for entry in file_error_markdown if entry.startswith("- [")
    ]
    socratic_assert(
        condition="**Documentation:**" in file_error_markdown
        and any(
            entry.startswith("- [File Handling Guide]") for entry in file_doc_entries
        ),
        question="Is documentation highlighted after file suggestions",
        expected="bold Documentation header present",
    )

    ui.display_result("WARNING: Keep an eye on resources")
    socratic_assert(
        condition=stub.warning_calls[-1] == "WARNING: Keep an eye on resources",
        question="Do WARNING-prefixed messages trigger Streamlit.warning",
        expected="warning() captures the prefixed alert",
    )

    ui.display_result("SUCCESS: Workflow stabilized")
    socratic_assert(
        condition=stub.success_calls[-1] == "SUCCESS: Workflow stabilized",
        question="Are SUCCESS-prefixed messages routed to success()",
        expected="success channel records the prefixed outcome",
    )

    ui.display_result("# Primary Heading")
    ui.display_result("## Secondary Heading")
    ui.display_result("### Deep Heading")
    socratic_assert(
        condition=stub.header_calls[-1] == "Primary Heading",
        question="Do single hashes yield header() invocations",
        expected="header() receives the stripped text",
    )
    socratic_assert(
        condition=stub.subheader_calls[-1] == "Secondary Heading",
        question="Does a double hash promote the subheader channel",
        expected="subheader() renders the secondary text",
    )
    socratic_assert(
        condition=stub.markdown_calls[-1] == "**Deep Heading**",
        question="Are deeper headings emitted as bold markdown",
        expected="double-asterisk formatting wraps the text",
    )

    ui.display_result("Plain details")
    socratic_assert(
        condition=stub.write_calls[-1] == "Plain details",
        question="Is the fallback writer used for general messages",
        expected="write() receives the plain text",
    )

    webui.WebUI.display_result(ui, "Plain details (unbound)")
    socratic_assert(
        condition=stub.write_calls[-1] == "Plain details (unbound)",
        question="Does invoking display_result via the class still reach write()",
        expected="write() captures the unbound invocation",
    )


def test_render_traceback_captures_output(monkeypatch: pytest.MonkeyPatch) -> None:
    """Traceback rendering opens an expander and streams the code block."""

    stub = install_streamlit_stub(monkeypatch)
    ui = webui.WebUI()

    ui._render_traceback("Traceback (most recent call last)")

    socratic_assert(
        condition=bool(stub.expanders)
        and stub.code_calls[-1][0] == "Traceback (most recent call last)",
        question="Does the traceback expander capture the diagnostic text",
        expected="expander records the traceback code block",
    )

    webui.WebUI._render_traceback(ui, "Traceback via class")
    socratic_assert(
        condition=stub.code_calls[-1][0] == "Traceback via class",
        question="Does the unbound traceback renderer delegate through the expander",
        expected="expander captures the class-level invocation",
    )


def test_error_mapping_helpers_cover_cases() -> None:
    """Error type and helper tables provide consistent guidance across keywords."""

    ui = webui.WebUI()

    mapping = {
        "File not found": "file_not_found",
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

    for message, expected in mapping.items():
        socratic_assert(
            condition=ui._get_error_type(message) == expected,
            question=f"Does '{message}' map to the documented error type",
            expected=expected,
        )

    socratic_assert(
        condition=ui._get_error_type("no match") == "",
        question="What happens when no keywords are present",
        expected="empty error type",
    )

    suggestions = ui._get_error_suggestions("api_error")
    socratic_assert(
        condition="Verify that your API key is valid" in suggestions,
        question="Are API error suggestions populated",
        expected="API key guidance present",
    )

    docs = ui._get_documentation_links("api_error")
    socratic_assert(
        condition="API Integration Guide" in docs,
        question="Are API documentation links available",
        expected="API Integration Guide link returned",
    )


def test_ui_progress_estimates_and_subtasks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Progress lifecycle mirrors CLI telemetry with sanitized subtasks."""

    stub = install_streamlit_stub(monkeypatch)
    times = count(start=0, step=10)
    monkeypatch.setattr(webui.time, "time", lambda: next(times))

    ui = webui.WebUI()
    indicator = ui.create_progress("<b>Deploy</b>", total=4)

    status_container, time_container = stub.empty_containers[:2]
    socratic_assert(
        condition=status_container.markdown_calls[0]
        == "**&lt;b&gt;Deploy&lt;/b&gt;** - 0%",
        question="Is the initial progress description sanitized and formatted",
        expected="bold sanitized label with 0%",
    )

    indicator.update()
    socratic_assert(
        condition=status_container.markdown_calls[-1]
        == "**&lt;b&gt;Deploy&lt;/b&gt;** - 25%",
        question="Does the first update reach 25% with sanitized text",
        expected="25% status entry",
    )
    socratic_assert(
        condition=time_container.info_calls[-1] == "ETA: 30 seconds",
        question="Is ETA computed from update cadence",
        expected="30 second projection",
    )

    indicator.update(status="Almost <done>")
    socratic_assert(
        condition=indicator._status == "Almost &lt;done&gt;",
        question="Are explicit status overrides sanitized",
        expected="escaped HTML in status",
    )
    socratic_assert(
        condition=stub.progress_bars[0].values[-1] == 0.5,
        question="Does the main progress bar reach 50% after two updates",
        expected="0.5 progress fraction",
    )

    subtask_id = indicator.add_subtask("Phase <one>", total=2)
    sub_container = stub.containers[0]
    socratic_assert(
        condition=sub_container.markdown_calls[-1]
        == "&nbsp;&nbsp;&nbsp;&nbsp;**Phase &lt;one&gt;** - 0%",
        question="Are subtask descriptions sanitized and indented",
        expected="HTML-escaped subtask label",
    )

    indicator.update_subtask(subtask_id, description="Halfway <mark>")
    socratic_assert(
        condition=sub_container.markdown_calls[-1]
        == "&nbsp;&nbsp;&nbsp;&nbsp;**Halfway &lt;mark&gt;** - 50%",
        question="Do subtask updates preserve sanitation and percentage",
        expected="50% sanitized subtask",
    )

    indicator._update_subtask_display("missing-task")
    socratic_assert(
        condition=sub_container.markdown_calls[-1]
        == "&nbsp;&nbsp;&nbsp;&nbsp;**Halfway &lt;mark&gt;** - 50%",
        question="Does an unknown subtask leave existing markdown untouched",
        expected="no new markdown entries for missing task",
    )

    indicator.update_subtask("missing-task")
    socratic_assert(
        condition=sub_container.markdown_calls[-1]
        == "&nbsp;&nbsp;&nbsp;&nbsp;**Halfway &lt;mark&gt;** - 50%",
        question="Do updates to unknown subtasks short-circuit without mutation",
        expected="progress list remains unchanged for missing task",
    )

    indicator.complete_subtask(subtask_id)
    socratic_assert(
        condition=sub_container.success_calls[-1] == "Completed: Halfway &lt;mark&gt;",
        question="Does completing a subtask emit a success message",
        expected="Completed message with escaped markup",
    )

    indicator.complete_subtask("missing-task")
    socratic_assert(
        condition=sub_container.success_calls[-1] == "Completed: Halfway &lt;mark&gt;",
        question="Do missing subtasks skip completion handling",
        expected="no additional success calls for invalid task id",
    )

    indicator.complete()
    socratic_assert(
        condition=stub.progress_bars[0].values[-1] == 1.0,
        question="Does completion drive the main progress bar to 100%",
        expected="progress value of 1.0",
    )
    socratic_assert(
        condition=stub.success_calls[-1] == "Completed: &lt;b&gt;Deploy&lt;/b&gt;",
        question="Is the final success message sanitized",
        expected="escaped deployment label",
    )


def test_ui_progress_complete_cascades_and_falls_back_to_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Completing the root task finalizes subtasks and falls back when ``success`` is absent."""

    monkeypatch.delattr(BehaviorStreamlitStub, "success")
    stub = install_streamlit_stub(monkeypatch)
    times = iter(range(0, 20))
    monkeypatch.setattr(webui.time, "time", lambda: next(times))

    ui = webui.WebUI()
    indicator = ui.create_progress("Compile <artifact>", total=2)
    subtask_id = indicator.add_subtask("Subtask <one>", total=1)

    socratic_assert(
        condition=subtask_id in indicator._subtasks,
        question="Did the subtask register before completion",
        expected="subtask identifier stored in the progress tracker",
    )

    indicator.complete()

    socratic_assert(
        condition=stub.write_calls[-1] == "Completed: Compile &lt;artifact&gt;",
        question="Does the absence of Streamlit.success fall back to write()",
        expected="sanitized completion message routed through write()",
    )

    sub_container = stub.containers[0]
    socratic_assert(
        condition=sub_container.success_calls[-1] == "Completed: Subtask &lt;one&gt;",
        question="Were subtasks completed automatically when the root finishes",
        expected="cascaded completion recorded on the subtask container",
    )


def test_ui_progress_eta_formats_hours(monkeypatch: pytest.MonkeyPatch) -> None:
    """Long running tasks display hour-level ETAs."""

    stub = install_streamlit_stub(monkeypatch)
    times = iter([0, 1000, 2000, 3000, 4000, 5000])
    monkeypatch.setattr(webui.time, "time", lambda: next(times))

    ui = webui.WebUI()
    indicator = ui.create_progress("Long task", total=5)

    indicator.update()

    time_container = stub.empty_containers[1]
    socratic_assert(
        condition=time_container.info_calls[-1] == "ETA: 1 hours, 6 minutes",
        question="Do ETAs longer than an hour display hours and minutes",
        expected="hours/minutes ETA string",
    )


def test_ui_progress_status_transitions_cover_all_thresholds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Status messages progress from starting through completion with sanitized text."""

    stub = install_streamlit_stub(monkeypatch)
    times = iter(range(0, 40))
    monkeypatch.setattr(webui.time, "time", lambda: next(times))

    ui = webui.WebUI()
    indicator = ui.create_progress("Compile <project>", total=100)

    socratic_assert(
        condition=indicator._description == "Compile &lt;project&gt;",
        question="Is the initial progress description sanitized on creation",
        expected="HTML entities escaped in the stored description",
    )

    indicator.update(advance=25)
    socratic_assert(
        condition=indicator._status == "Processing...",
        question="Does reaching 25% progress promote the Processing status",
        expected="status transitions from Starting to Processing",
    )

    indicator.update(advance=25)
    socratic_assert(
        condition=indicator._status == "Halfway there...",
        question="Is the halfway checkpoint labeled correctly",
        expected="status reads 'Halfway there...' at 50%",
    )

    indicator.update(advance=25)
    socratic_assert(
        condition=indicator._status == "Almost done...",
        question="Does exceeding 75% announce the almost-done phase",
        expected="status string switches to 'Almost done...'",
    )

    indicator.update(advance=24, description="Final <polish>")
    socratic_assert(
        condition=indicator._status == "Finalizing...",
        question="Do near-complete updates surface the finalizing status",
        expected="status shows 'Finalizing...' before completion",
    )
    socratic_assert(
        condition=indicator._description == "Final &lt;polish&gt;",
        question="Are update descriptions sanitized when overriding text",
        expected="HTML entities escaped in the stored description",
    )

    subtask_id = indicator.add_subtask("Document <phase>", total=10)
    indicator.update_subtask(subtask_id, advance=5)
    indicator.complete_subtask(subtask_id)
    indicator.complete()

    socratic_assert(
        condition=stub.success_calls[-1] == "Completed: Final &lt;polish&gt;",
        question="Does completion announce the sanitized description",
        expected="success() emits the escaped final message",
    )
    socratic_assert(
        condition=stub.progress_bars[0].values[-1] == 1.0,
        question="Does the primary progress bar reach full completion",
        expected="progress value equals 1.0 after complete()",
    )


def test_ui_progress_eta_minutes_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Slow progress projections report minute-level ETAs."""

    stub = install_streamlit_stub(monkeypatch)
    times = iter(range(0, 10))
    monkeypatch.setattr(webui.time, "time", lambda: next(times))

    ui = webui.WebUI()
    indicator = ui.create_progress("Slow compile", total=5)
    indicator.update(advance=0.01)

    time_container = stub.empty_containers[1]
    socratic_assert(
        condition=time_container.info_calls[-1] == "ETA: 8 minutes",
        question="Does the ETA calculator switch to minutes for long projections",
        expected="ETA string reports minutes when exceeding sixty seconds",
    )


@pytest.mark.parametrize(
    ("screen_width", "expected_columns", "expected_mobile"),
    [
        (500, 1, True),
        (800, 2, False),
        (1300, 3, False),
        ("absent", 3, False),
    ],
)
def test_get_layout_config_breakpoints(
    monkeypatch: pytest.MonkeyPatch,
    screen_width: int | str,
    expected_columns: int,
    expected_mobile: bool,
) -> None:
    """Layout config responds to breakpoints and missing measurements."""

    stub = install_streamlit_stub(monkeypatch)
    ui = webui.WebUI()

    if screen_width == "absent":
        if hasattr(stub.session_state, "screen_width"):
            delattr(stub.session_state, "screen_width")
    else:
        stub.session_state.screen_width = screen_width

    config = ui.get_layout_config()
    socratic_assert(
        condition=config["columns"] == expected_columns,
        question="How many columns does the layout expose at this breakpoint",
        expected=f"{expected_columns} columns",
    )
    socratic_assert(
        condition=config["is_mobile"] is expected_mobile,
        question="Does the mobile flag reflect the expected breakpoint",
        expected=str(expected_mobile),
    )


def test_run_responsive_layout_and_router_invocation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`run()` applies defaults, injects resize JS, and invokes the router."""

    stub = install_streamlit_stub(monkeypatch)

    navigation = {"Home": lambda: None}
    monkeypatch.setattr(webui.WebUI, "navigation_items", lambda self: navigation)

    router_calls: list[str] = []

    class RouterSpy:
        def __init__(
            self, owner: webui.WebUI, pages: dict[str, Callable[[], None]]
        ) -> None:
            router_calls.append("init")

        def run(self) -> None:
            router_calls.append("run")

    monkeypatch.setattr(webui, "Router", RouterSpy)

    ui = webui.WebUI()
    ui.run()

    socratic_assert(
        condition=hasattr(stub.session_state, "screen_width")
        and stub.session_state.screen_width == 1200,
        question="Does run() seed the default screen width when missing",
        expected="screen_width=1200",
    )
    socratic_assert(
        condition=stub.session_state.screen_height == 800,
        question="Is the default screen height populated alongside width",
        expected="screen_height=800 during initialization",
    )
    socratic_assert(
        condition=any(
            call.lstrip().startswith("<style>") for call in stub.markdown_calls
        ),
        question="Is the responsive CSS injected before rendering",
        expected="inline <style> block",
    )
    socratic_assert(
        condition=any(".stButton>button" in call for call in stub.markdown_calls),
        question="Does the injected CSS customize Streamlit buttons",
        expected=".stButton>button selector present in stylesheet",
    )
    socratic_assert(
        condition=stub.sidebar.title_calls[-1] == "DevSynth",
        question="Does the sidebar title remain accessible after resize wiring",
        expected="DevSynth title rendered",
    )
    socratic_assert(
        condition=bool(stub.html_calls),
        question="Is the resize JavaScript injected via components.html",
        expected="recorded html() invocation",
    )
    socratic_assert(
        condition=router_calls == ["init", "run"],
        question="Is the router created lazily and executed once",
        expected="RouterSpy init then run",
    )


def test_run_handles_html_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """HTML injection failures surface as display_result messages."""

    stub = install_streamlit_stub(monkeypatch)
    navigation = {"Home": lambda: None}
    monkeypatch.setattr(webui.WebUI, "navigation_items", lambda self: navigation)

    def boom(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("component failure")

    stub.components.v1.html = boom  # type: ignore[assignment]

    messages: list[str] = []
    monkeypatch.setattr(
        webui.WebUI,
        "display_result",
        lambda self, message, **kwargs: messages.append(message),
        raising=False,
    )

    router_ran = False

    class RouterSpy:
        def __init__(
            self, owner: webui.WebUI, pages: dict[str, Callable[[], None]]
        ) -> None:
            pass

        def run(self) -> None:  # pragma: no cover - guarded by Socratic assertion
            nonlocal router_ran
            router_ran = True

    monkeypatch.setattr(webui, "Router", RouterSpy)

    ui = webui.WebUI()
    ui.run()

    socratic_assert(
        condition=messages[-1] == "ERROR: component failure",
        question="Are component HTML failures surfaced as errors",
        expected="ERROR-prefixed message",
    )
    socratic_assert(
        condition=router_ran is False,
        question="Does router execution halt when HTML injection fails",
        expected="router remains idle",
    )


def test_run_handles_page_config_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Configuration errors surface as WebUI messages without router execution."""

    stub = install_streamlit_stub(monkeypatch)
    stub.page_config_error = RuntimeError("No display")
    navigation = {"Home": lambda: None}
    monkeypatch.setattr(webui.WebUI, "navigation_items", lambda self: navigation)

    router_ran = False

    class RouterSpy:
        def __init__(
            self, owner: webui.WebUI, pages: dict[str, Callable[[], None]]
        ) -> None:
            pass

        def run(self) -> None:  # pragma: no cover - guarded by Socratic assertion
            nonlocal router_ran
            router_ran = True

    monkeypatch.setattr(webui, "Router", RouterSpy)

    messages: list[str] = []

    def record_display(
        self: webui.WebUI,
        message: str,
        *,
        highlight: bool = False,
        message_type: str | None = None,
    ) -> None:
        messages.append(message)

    monkeypatch.setattr(webui.WebUI, "display_result", record_display, raising=False)

    ui = webui.WebUI()
    ui.run()

    socratic_assert(
        condition=messages and messages[0].startswith("ERROR:"),
        question="Does run() surface page configuration failures",
        expected="an ERROR-prefixed message",
    )
    socratic_assert(
        condition=router_ran is False,
        question="Is router execution skipped when initialization fails",
        expected="router remains idle",
    )


def test_run_without_components_invokes_router(monkeypatch: pytest.MonkeyPatch) -> None:
    """Router still runs when components module is absent."""

    stub = install_streamlit_stub(monkeypatch)
    stub.components = None
    navigation = {"Docs": lambda: None}
    monkeypatch.setattr(webui.WebUI, "navigation_items", lambda self: navigation)

    router_calls: list[str] = []

    class RouterSpy:
        def __init__(
            self, owner: webui.WebUI, pages: dict[str, Callable[[], None]]
        ) -> None:
            router_calls.append("init")

        def run(self) -> None:
            router_calls.append("run")

    monkeypatch.setattr(webui, "Router", RouterSpy)

    ui = webui.WebUI()
    ui.run()

    socratic_assert(
        condition=router_calls == ["init", "run"],
        question="Does the router execute even when components are missing",
        expected="router invoked with fallback configuration",
    )


def test_ensure_router_caches_router_instance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`_ensure_router` only instantiates the router once."""

    install_streamlit_stub(monkeypatch)
    init_calls: list[str] = []

    class RouterSpy:
        def __init__(
            self, owner: webui.WebUI, pages: dict[str, Callable[[], None]]
        ) -> None:
            init_calls.append("init")

        def run(self) -> None:  # pragma: no cover - not exercised in this test
            raise AssertionError("run should not be called")

    monkeypatch.setattr(webui, "Router", RouterSpy)
    ui = webui.WebUI()
    first_router = ui._ensure_router()
    second_router = ui._ensure_router()

    socratic_assert(
        condition=init_calls == ["init"],
        question="How many router instances are constructed",
        expected="a single Router initialization",
    )
    socratic_assert(
        condition=first_router is second_router,
        question="Does _ensure_router reuse the cached router",
        expected="the same RouterSpy instance is returned",
    )


def test_run_module_entrypoint_invokes_webui_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The module-level run() helper instantiates WebUI and executes run()."""

    install_streamlit_stub(monkeypatch)
    call_sequence: list[str] = []

    class Runner(webui.WebUI):
        def run(self) -> None:  # type: ignore[override]
            call_sequence.append("run")

    monkeypatch.setattr(webui, "WebUI", Runner)
    webui.run()

    socratic_assert(
        condition=call_sequence == ["run"],
        question="Does the run() convenience function execute the WebUI runner",
        expected="Runner.run() is invoked once",
    )
