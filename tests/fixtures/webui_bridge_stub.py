"""Fixtures that coordinate Streamlit stubs across WebUI modules."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import pytest

from tests.fixtures.fake_streamlit import FakeStreamlit


@runtime_checkable
class SupportsStreamlitLike(Protocol):
    """Protocol capturing the small surface we rely on for Streamlit stubs."""

    session_state: Any  # pragma: no cover - attribute existence only


def _make_stub_factory(stub: SupportsStreamlitLike) -> Any:
    """Create a callable that consistently returns ``stub``."""

    def _return_stub() -> SupportsStreamlitLike:
        return stub

    return _return_stub


def install_streamlit_stub(
    stub: SupportsStreamlitLike, monkeypatch: pytest.MonkeyPatch
) -> SupportsStreamlitLike:
    """Install ``stub`` as the Streamlit implementation for WebUI modules."""

    from devsynth.interface import webui, webui_bridge, webui_state

    require_stub = _make_stub_factory(stub)

    monkeypatch.setattr(webui_bridge, "st", stub, raising=False)
    monkeypatch.setattr(webui_bridge, "_require_streamlit", require_stub, raising=False)

    monkeypatch.setattr(webui, "_STREAMLIT", stub, raising=False)
    monkeypatch.setattr(webui, "st", stub, raising=False)
    monkeypatch.setattr(webui, "_require_streamlit", require_stub, raising=False)

    monkeypatch.setattr(webui_state, "st", stub, raising=False)
    monkeypatch.setattr(webui_state, "_require_streamlit", require_stub, raising=False)

    return stub


@pytest.fixture
def streamlit_bridge_stub(
    monkeypatch: pytest.MonkeyPatch,
) -> SupportsStreamlitLike:
    """Provide a shared :class:`FakeStreamlit` instance for WebUI tests."""

    stub = FakeStreamlit()
    install_streamlit_stub(stub, monkeypatch)

    from devsynth.interface import webui_bridge

    assert webui_bridge._require_streamlit() is stub
    yield stub


__all__ = ["install_streamlit_stub", "streamlit_bridge_stub"]
