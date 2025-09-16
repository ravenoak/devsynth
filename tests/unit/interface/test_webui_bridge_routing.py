"""Focused tests for :mod:`devsynth.interface.webui_bridge` routing logic."""

from __future__ import annotations

import html

import pytest

from devsynth.interface import webui_bridge


class FakeStreamlit:
    """Collect calls made during WebUI bridge interactions."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def _record(self, channel: str, message: str) -> None:
        self.calls.append((channel, message))

    def write(self, message: str) -> None:
        self._record("write", message)

    def info(self, message: str) -> None:
        self._record("info", message)

    def warning(self, message: str) -> None:
        self._record("warning", message)

    def success(self, message: str) -> None:
        self._record("success", message)

    def error(self, message: str) -> None:
        self._record("error", message)


@pytest.mark.fast
def test_display_result_handshake_routes_to_streamlit(monkeypatch):
    """The bridge performs a Streamlit handshake before routing output."""

    fake_st = FakeStreamlit()
    handshake: list[str] = []

    def fake_require() -> FakeStreamlit:
        handshake.append("called")
        webui_bridge.st = fake_st
        return fake_st

    monkeypatch.setattr(webui_bridge, "_require_streamlit", fake_require)
    monkeypatch.setattr(webui_bridge, "st", None, raising=False)

    def passthrough(self, message: str, message_type=None, highlight=False):  # type: ignore[override]
        return message

    monkeypatch.setattr(webui_bridge.OutputFormatter, "format_message", passthrough)

    bridge = webui_bridge.WebUIBridge()
    bridge.display_result("hello world")

    assert handshake == ["called"]
    assert fake_st.calls == [("write", "hello world")]
    assert bridge.messages == ["hello world"]


@pytest.mark.fast
def test_display_result_error_route_sanitizes_output(monkeypatch):
    """Error messages are sanitized before reaching Streamlit."""

    fake_st = FakeStreamlit()
    handshake = {"count": 0}

    def fake_require() -> FakeStreamlit:
        handshake["count"] += 1
        webui_bridge.st = fake_st
        return fake_st

    monkeypatch.setenv("DEVSYNTH_SANITIZATION_ENABLED", "1")
    monkeypatch.setattr(webui_bridge, "_require_streamlit", fake_require)
    monkeypatch.setattr(webui_bridge, "st", None, raising=False)

    def passthrough(self, message: str, message_type=None, highlight=False):  # type: ignore[override]
        return message

    monkeypatch.setattr(webui_bridge.OutputFormatter, "format_message", passthrough)

    bridge = webui_bridge.WebUIBridge()
    bridge.display_result("<b>boom</b>", message_type="error")

    expected = html.escape("<b>boom</b>")
    assert handshake["count"] == 1
    assert fake_st.calls == [("error", expected)]
    assert bridge.messages == [expected]


@pytest.mark.fast
def test_display_result_respects_sanitization_flag(monkeypatch):
    """Sanitization can be disabled for trusted environments."""

    fake_st = FakeStreamlit()
    handshake = {"count": 0}

    def fake_require() -> FakeStreamlit:
        handshake["count"] += 1
        webui_bridge.st = fake_st
        return fake_st

    monkeypatch.setenv("DEVSYNTH_SANITIZATION_ENABLED", "0")
    monkeypatch.setattr(webui_bridge, "_require_streamlit", fake_require)
    monkeypatch.setattr(webui_bridge, "st", None, raising=False)

    def passthrough(self, message: str, message_type=None, highlight=False):  # type: ignore[override]
        return message

    monkeypatch.setattr(webui_bridge.OutputFormatter, "format_message", passthrough)

    bridge = webui_bridge.WebUIBridge()
    raw = "<script>alert('x')</script>"
    bridge.display_result(raw, message_type="info")

    assert handshake["count"] == 1
    assert fake_st.calls == [("info", raw)]
    assert bridge.messages == [raw]


@pytest.mark.fast
def test_display_result_highlight_routes_to_info(monkeypatch):
    """Highlighted messages route through Streamlit ``info`` after handshake."""

    fake_st = FakeStreamlit()
    handshake = {"count": 0}

    def fake_require() -> FakeStreamlit:
        handshake["count"] += 1
        webui_bridge.st = fake_st
        return fake_st

    monkeypatch.setattr(webui_bridge, "_require_streamlit", fake_require)
    monkeypatch.setattr(webui_bridge, "st", None, raising=False)

    def passthrough(self, message: str, message_type=None, highlight=False):  # type: ignore[override]
        return message

    monkeypatch.setattr(webui_bridge.OutputFormatter, "format_message", passthrough)

    bridge = webui_bridge.WebUIBridge()
    message = "<b>highlight me</b>"
    bridge.display_result(message, highlight=True)

    expected = html.escape(message)
    assert handshake["count"] == 1
    assert ("info", expected) in fake_st.calls
    assert bridge.messages == [expected]


@pytest.mark.fast
def test_display_result_success_routes_to_success(monkeypatch):
    """Success messages route to Streamlit ``success`` channel."""

    fake_st = FakeStreamlit()
    handshake = {"count": 0}

    def fake_require() -> FakeStreamlit:
        handshake["count"] += 1
        webui_bridge.st = fake_st
        return fake_st

    monkeypatch.setattr(webui_bridge, "_require_streamlit", fake_require)
    monkeypatch.setattr(webui_bridge, "st", None, raising=False)

    def passthrough(self, message: str, message_type=None, highlight=False):  # type: ignore[override]
        return message

    monkeypatch.setattr(webui_bridge.OutputFormatter, "format_message", passthrough)

    bridge = webui_bridge.WebUIBridge()
    bridge.display_result("<em>done</em>", message_type="success")

    expected = html.escape("<em>done</em>")
    assert handshake["count"] == 1
    assert ("success", expected) in fake_st.calls
    assert bridge.messages == [expected]
