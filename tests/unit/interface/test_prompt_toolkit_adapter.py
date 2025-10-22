"""Unit tests for the prompt-toolkit adapter."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Callable

import pytest

from devsynth.interface.prompt_toolkit_adapter import (
    PromptToolkitAdapter,
    PromptToolkitComponents,
)


pytestmark = [pytest.mark.fast]


class StubHistory:
    """Trivial history container used for adapter tests."""

    def __init__(self) -> None:
        self.entries: list[str] = []


class StubSession:
    """Prompt session that replays predefined responses."""

    def __init__(self, *, responses: list[str] | None = None, history: StubHistory | None = None) -> None:
        self.history = history or StubHistory()
        self.responses = list(responses or [])
        self.prompt_calls: list[tuple[str, dict[str, object]]] = []
        self.app = SimpleNamespace(output=SimpleNamespace(write=lambda *_: None))

    def prompt(self, message: str, default: str = "", **kwargs: object) -> str:
        self.prompt_calls.append((message, kwargs))
        if self.responses:
            return self.responses.pop(0)
        return default


class StubCompleter:
    """Record the completions that would be offered to the user."""

    def __init__(self, words: list[str], ignore_case: bool = True) -> None:
        self.words = list(words)
        self.ignore_case = ignore_case


class StubStyle:
    """Simplistic style stub matching the prompt-toolkit API."""

    @classmethod
    def from_dict(cls, mapping: dict[str, str]) -> "StubStyle":
        instance = cls()
        instance.mapping = mapping
        return instance


class StubCompleteStyle:
    """Enumeration stub exposing the MULTI_COLUMN attribute."""

    MULTI_COLUMN = "multi-column"


def _components(session_cls: Callable[..., StubSession]) -> PromptToolkitComponents:
    return PromptToolkitComponents(
        prompt_session_class=session_cls,
        history_class=StubHistory,
        word_completer_class=StubCompleter,
        radiolist_dialog=lambda **_: SimpleNamespace(run=lambda: "beta"),
        checkboxlist_dialog=lambda **_: SimpleNamespace(run=lambda: ["alpha", "beta"]),
        style_class=StubStyle,
        complete_style_enum=StubCompleteStyle,
    )


def test_prompt_text_prefers_dialog_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    """The adapter should return dialog selections without hitting the session."""

    session = StubSession()
    components = _components(lambda history: session)
    adapter = PromptToolkitAdapter(components=components, session=session)

    result = adapter.prompt_text("Pick one", choices=["alpha", "beta"], default="alpha")

    assert result == "beta"
    assert session.prompt_calls == []


def test_prompt_text_validates_input(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid responses trigger re-prompts until validator succeeds."""

    session = StubSession(responses=["", "valid"])
    components = _components(lambda history: session)
    adapter = PromptToolkitAdapter(components=components, session=session)

    recorded_messages: list[str] = []
    monkeypatch.setattr(adapter, "_emit_validation_message", recorded_messages.append)

    result = adapter.prompt_text(
        "Enter value",
        default=None,
        validator=lambda text: bool(text.strip()),
    )

    assert result == "valid"
    # First prompt should have been replayed with validator feedback.
    assert len(session.prompt_calls) == 2
    assert recorded_messages[-1].startswith("Invalid input")


def test_prompt_multi_select_returns_checkbox_choices() -> None:
    """Multi-select dialog values should be returned as strings."""

    session = StubSession()
    components = _components(lambda history: session)
    adapter = PromptToolkitAdapter(components=components, session=session)

    result = adapter.prompt_multi_select(
        "Select features",
        options=[("alpha", "Alpha"), ("beta", "Beta")],
        default=["gamma"],
    )

    assert result == ["alpha", "beta"]
