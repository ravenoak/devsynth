from __future__ import annotations

import importlib
import sys
from types import ModuleType, SimpleNamespace
from typing import Any, Dict, Tuple
from collections.abc import Callable

import pytest

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("force_webui_available")]


class StreamlitRecorder(ModuleType):
    """Minimal Streamlit stub that records message routing for assertions."""

    def __init__(self) -> None:
        super().__init__("streamlit")
        self.error_messages: list[Any] = []
        self.warning_messages: list[Any] = []
        self.success_messages: list[Any] = []
        self.info_messages: list[Any] = []
        self.write_messages: list[Any] = []
        self.markdown_calls: list[tuple[Any, tuple[Any, ...], dict[str, Any]]] = []

    def error(self, message: Any, *args: Any, **kwargs: Any) -> None:
        self.error_messages.append(message)

    def warning(self, message: Any, *args: Any, **kwargs: Any) -> None:
        self.warning_messages.append(message)

    def success(self, message: Any, *args: Any, **kwargs: Any) -> None:
        self.success_messages.append(message)

    def info(self, message: Any, *args: Any, **kwargs: Any) -> None:
        self.info_messages.append(message)

    def write(self, message: Any, *args: Any, **kwargs: Any) -> None:
        self.write_messages.append(message)

    def markdown(self, message: Any, *args: Any, **kwargs: Any) -> None:
        self.markdown_calls.append((message, args, kwargs))

    def __getattr__(self, name: str) -> Any:  # pragma: no cover - defensive fallback
        def _noop(*_args: Any, **_kwargs: Any) -> None:
            return None

        return _noop


@pytest.fixture()
def webui_bridge_module(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[ModuleType, StreamlitRecorder]:
    """Reload the WebUI bridge module against the recorder stub."""

    streamlit_stub = StreamlitRecorder()
    monkeypatch.setitem(sys.modules, "streamlit", streamlit_stub)

    import devsynth.interface.webui_bridge as bridge

    importlib.reload(bridge)
    return bridge, streamlit_stub


class BadString:
    """Object whose string conversion always fails to exercise fallbacks."""

    def __str__(self) -> str:  # pragma: no cover - exercised indirectly
        raise RuntimeError("string conversion not supported")


def test_nested_subtask_handles_fallbacks_and_missing_parents(
    webui_bridge_module: tuple[ModuleType, StreamlitRecorder],
) -> None:
    """Nested subtasks fall back to safe labels and ignore missing parents."""

    bridge, _ = webui_bridge_module
    indicator = bridge.WebUIProgressIndicator("Main task", 10)

    parent_id = indicator.add_subtask(BadString(), total=5)
    parent = indicator._subtasks[parent_id]
    assert parent["description"] == "<subtask>"

    nested_id = indicator.add_nested_subtask(parent_id, BadString(), total=4)
    nested = parent["nested_subtasks"][nested_id]
    assert nested["description"] == "<nested subtask>"

    nested_before = dict(nested)
    indicator.update_nested_subtask(
        parent_id, nested_id, description=BadString(), advance=0
    )
    assert nested["description"] == nested_before["description"]
    assert nested["current"] == nested_before["current"]

    indicator.update_nested_subtask(parent_id, nested_id, status=BadString(), advance=0)
    assert nested["status"] == "In progress..."

    assert indicator.add_nested_subtask("missing", "child") == ""

    indicator.update_nested_subtask("missing", nested_id, description="ignored")
    indicator.update_nested_subtask(parent_id, "missing", status="ignored")

    indicator.complete_nested_subtask("missing", nested_id)
    indicator.complete_nested_subtask(parent_id, "missing")

    indicator.complete_nested_subtask(parent_id, nested_id)
    assert nested["completed"] is True
    assert nested["current"] == nested["total"]
    assert nested["status"] == "Complete"


def test_nested_subtask_status_progression_without_explicit_status(
    webui_bridge_module: tuple[ModuleType, StreamlitRecorder],
) -> None:
    """Omitting ``status`` triggers the automatic status lifecycle."""

    bridge, _ = webui_bridge_module
    indicator = bridge.WebUIProgressIndicator("Main task", 100)
    parent_id = indicator.add_subtask("Parent", total=100)
    nested_id = indicator.add_nested_subtask(parent_id, "Child", total=100)
    nested = indicator._subtasks[parent_id]["nested_subtasks"][nested_id]

    def status_for(current: int) -> str:
        nested["current"] = current
        indicator.update_nested_subtask(parent_id, nested_id, advance=0)
        return nested["status"]

    assert status_for(0) == "Starting..."
    assert status_for(25) == "Processing..."
    assert status_for(50) == "Halfway there..."
    assert status_for(75) == "Almost done..."
    assert status_for(99) == "Finalizing..."
    assert status_for(100) == "Complete"


def test_wizard_helpers_normalize_mixed_inputs(
    webui_bridge_module: tuple[ModuleType, StreamlitRecorder],
) -> None:
    """Wizard navigation tolerates strings, floats, and invalid totals."""

    bridge, _ = webui_bridge_module
    adjust = bridge.WebUIBridge.adjust_wizard_step
    normalize = bridge.WebUIBridge.normalize_wizard_step

    assert adjust(1, direction="next", total=3) == 2
    assert adjust(2, direction="next", total=3) == 2
    assert adjust("2", direction="back", total=5) == 1
    assert adjust("bad", direction="next", total=-4) == 0
    assert adjust(0, direction="back", total=2) == 0
    assert adjust(1, direction="stay", total=4) == 1

    assert normalize("3", total=5) == 3
    assert normalize("3.9", total=5) == 3
    assert normalize(7, total=5) == 4
    assert normalize(2.3, total=5) == 2
    assert normalize("", total=5) == 0
    assert normalize(None, total=5) == 0
    assert normalize("bad", total=0) == 0


def test_prompt_helpers_echo_defaults(
    webui_bridge_module: tuple[ModuleType, StreamlitRecorder],
) -> None:
    """The lightweight prompt helpers return the provided defaults."""

    bridge, _ = webui_bridge_module
    ui = bridge.WebUIBridge()

    assert ui.ask_question("Favorite tool?", default="DevSynth") == "DevSynth"
    assert ui.ask_question("Answer?", default=7) == "7"
    assert ui.ask_question("Empty?", default=None) == ""
    assert ui.confirm_choice("Continue?", default=True) is True
    assert ui.confirm_choice("Stop?", default=False) is False


def test_display_result_appends_documentation_links(
    webui_bridge_module: tuple[ModuleType, StreamlitRecorder],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Error messages surface documentation links provided by resolvers."""

    bridge, streamlit_stub = webui_bridge_module

    def format_with_docs(
        self,
        message: str,
        *,
        highlight: bool = False,
        message_type: str | None = None,
    ) -> str:
        resolver: Callable[[str], dict[str, str]] | None = getattr(
            self, "error_type_resolver", None
        )
        doc_links: dict[str, str] = {}
        if message_type == "error" and callable(resolver):
            doc_links = resolver(message)
        if doc_links:
            joined = "\n".join(f"- {title}: {url}" for title, url in doc_links.items())
            return f"{message}\nDocumentation:\n{joined}"
        return message

    monkeypatch.setattr(bridge.WebUIBridge, "_format_for_output", format_with_docs)

    ui = bridge.WebUIBridge()
    ui.error_type_resolver = lambda _: {"User Guide": "https://example.invalid/docs"}

    ui.display_result("Boom", message_type="error")

    assert streamlit_stub.error_messages == [
        "Boom\nDocumentation:\n- User Guide: https://example.invalid/docs",
    ]
    assert "https://example.invalid/docs" in ui.messages[-1]


def test_require_streamlit_caches_and_guides(
    webui_bridge_module: tuple[ModuleType, StreamlitRecorder],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``_require_streamlit`` caches successes and surfaces install help."""

    bridge, _ = webui_bridge_module

    monkeypatch.setattr(bridge, "st", None, raising=False)
    sentinel = object()
    imports: list[str] = []

    def fake_import(name: str) -> object:
        imports.append(name)
        return sentinel

    monkeypatch.setattr(importlib, "import_module", fake_import)

    bridge._require_streamlit()
    assert bridge.st is sentinel
    bridge._require_streamlit()
    assert imports == ["streamlit"]

    monkeypatch.setattr(bridge, "st", None, raising=False)

    def boom(_name: str) -> None:
        raise ImportError("missing streamlit")

    monkeypatch.setattr(importlib, "import_module", boom)

    with pytest.raises(bridge.DevSynthError) as excinfo:
        bridge._require_streamlit()

    assert "poetry install --with dev --extras webui" in str(excinfo.value)


def test_wizard_clamps_handle_invalid_inputs(
    webui_bridge_module: tuple[ModuleType, StreamlitRecorder],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Wizard helpers normalize mixed types and clamp to valid ranges."""

    bridge, _ = webui_bridge_module
    assert bridge.WebUIBridge.adjust_wizard_step(2, direction="next", total=2) == 1
    with caplog.at_level("WARNING"):
        assert (
            bridge.WebUIBridge.adjust_wizard_step("bad", direction="back", total=3) == 0
        )
    with caplog.at_level("WARNING"):
        assert (
            bridge.WebUIBridge.adjust_wizard_step(1, direction="sideways", total=-4)
            == 0
        )

    assert bridge.WebUIBridge.normalize_wizard_step(9, total=3) == 2
    with caplog.at_level("WARNING"):
        assert bridge.WebUIBridge.normalize_wizard_step("oops", total=3) == 0

    messages = [record.message for record in caplog.records]
    assert any("Invalid current step" in message for message in messages)
    assert any("Invalid total steps" in message for message in messages)
    assert any("Invalid direction" in message for message in messages)
    assert any("Failed to normalize step value" in message for message in messages)


def test_display_result_and_progress_use_formatter(
    webui_bridge_module: tuple[ModuleType, StreamlitRecorder],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Messages and progress reuse the shared ``OutputFormatter`` pipeline."""

    bridge, streamlit_stub = webui_bridge_module
    ui = bridge.WebUIBridge()

    formatter_calls: list[tuple[str, str | None, bool]] = []

    def fake_format(
        message: str, *, message_type: str | None = None, highlight: bool = False
    ) -> str:
        formatter_calls.append((message, message_type, highlight))
        return f"{message_type or 'normal'}::{highlight}::{message}"

    monkeypatch.setattr(
        ui,
        "formatter",
        SimpleNamespace(
            format_message=lambda message, message_type=None, highlight=False: fake_format(
                message,
                message_type=message_type,
                highlight=highlight,
            )
        ),
        raising=False,
    )

    ui.display_result("serious", message_type="error", highlight=True)
    ui.display_result("heads-up", message_type="warning")
    ui.display_result("success", message_type="success")
    ui.display_result("note", message_type="info")
    ui.display_result("plain")

    assert formatter_calls == [
        ("serious", "error", True),
        ("heads-up", "warning", False),
        ("success", "success", False),
        ("note", "info", False),
        ("plain", None, False),
    ]
    assert streamlit_stub.error_messages == ["error::True::serious"]
    assert streamlit_stub.warning_messages == ["warning::False::heads-up"]
    assert streamlit_stub.success_messages == ["success::False::success"]
    assert streamlit_stub.info_messages == ["info::False::note"]
    assert streamlit_stub.write_messages == ["normal::False::plain"]

    monkeypatch.setattr(
        bridge,
        "WebUIProgressIndicator",
        lambda description, total: ("indicator", description, total),
    )
    assert ui.create_progress("Deploy", total=3) == ("indicator", "Deploy", 3)


def test_display_result_highlight_falls_back_to_write(
    webui_bridge_module: tuple[ModuleType, StreamlitRecorder],
) -> None:
    """Highlight routing uses ``write`` when ``info`` is unavailable."""

    bridge, _ = webui_bridge_module
    ui = bridge.WebUIBridge()

    class MinimalStreamlit:
        def __init__(self) -> None:
            self.write_messages: list[str] = []

        def write(self, message: str, *args: object, **kwargs: object) -> None:
            self.write_messages.append(message)

    fallback_stub = MinimalStreamlit()
    original_st = bridge.st
    bridge.st = fallback_stub
    try:
        ui.display_result("Heads-up", highlight=True)
    finally:
        bridge.st = original_st

    assert len(fallback_stub.write_messages) == 1
    recorded = fallback_stub.write_messages[0]
    if hasattr(recorded, "renderable"):
        assert "Heads-up" in str(recorded.renderable)
    else:
        assert recorded == "Heads-up"
