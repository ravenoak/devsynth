from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.edrr.coordinator import PersistenceMixin
from devsynth.methodology.base import Phase

pytestmark = pytest.mark.fast


class StubPersistence(PersistenceMixin):
    """Minimal persistence adapter for exercising mixin helpers."""

    def __init__(self, memory_manager: MagicMock | None) -> None:
        self.memory_manager = memory_manager
        self.cycle_id = "cycle"
        self._preserved_context = {"EXPAND": {"notes": "state"}}


def test_safe_store_handles_missing_memory_manager() -> None:
    """ReqID: N/A"""

    stub = StubPersistence(memory_manager=None)
    assert stub._safe_store_with_edrr_phase({}, "CONTEXT", "EXPAND") is None


def test_safe_store_flushes_on_success() -> None:
    """ReqID: N/A"""

    memory_manager = MagicMock()
    memory_manager.store_with_edrr_phase.return_value = "mid"
    stub = StubPersistence(memory_manager)
    result = stub._safe_store_with_edrr_phase({}, "CONTEXT", "EXPAND")
    assert result == "mid"
    memory_manager.flush_updates.assert_called_once()


def test_safe_store_handles_errors() -> None:
    """ReqID: N/A"""

    memory_manager = MagicMock()
    memory_manager.store_with_edrr_phase.side_effect = RuntimeError("boom")
    stub = StubPersistence(memory_manager)
    assert stub._safe_store_with_edrr_phase({}, "CONTEXT", "EXPAND") is None


def test_safe_store_flush_failure_does_not_raise() -> None:
    """ReqID: N/A"""

    memory_manager = MagicMock()
    memory_manager.store_with_edrr_phase.return_value = "mid"
    memory_manager.flush_updates.side_effect = RuntimeError("flush boom")
    stub = StubPersistence(memory_manager)

    assert stub._safe_store_with_edrr_phase({}, "CONTEXT", "EXPAND") == "mid"


def test_safe_retrieve_normalizes_outputs() -> None:
    """ReqID: N/A"""

    memory_manager = MagicMock()
    memory_manager.retrieve_with_edrr_phase.side_effect = [
        ["item"],
        {"value": 1},
        None,
    ]
    stub = StubPersistence(memory_manager)
    assert stub._safe_retrieve_with_edrr_phase("TYPE", "EXPAND") == {"items": ["item"]}
    assert stub._safe_retrieve_with_edrr_phase("TYPE", "EXPAND") == {"value": 1}
    assert stub._safe_retrieve_with_edrr_phase("TYPE", "EXPAND") == {}


def test_safe_retrieve_missing_manager_returns_empty() -> None:
    """ReqID: N/A"""

    stub = StubPersistence(memory_manager=None)
    assert stub._safe_retrieve_with_edrr_phase("TYPE", "EXPAND") == {}


def test_safe_retrieve_without_support_returns_empty() -> None:
    """ReqID: N/A"""

    memory_manager = type("NoRetrieve", (), {})()
    stub = StubPersistence(memory_manager=memory_manager)

    assert stub._safe_retrieve_with_edrr_phase("TYPE", "EXPAND") == {}


def test_persist_context_snapshot_stores_context() -> None:
    """ReqID: N/A"""

    memory_manager = MagicMock()
    stub = StubPersistence(memory_manager)
    with patch.object(stub, "_safe_store_with_edrr_phase") as store:
        stub._persist_context_snapshot(Phase.EXPAND)
    store.assert_called_once()


def test_persist_context_snapshot_uses_deep_copy() -> None:
    """ReqID: N/A"""

    memory_manager = MagicMock()
    stub = StubPersistence(memory_manager)
    stub._preserved_context = {"EXPAND": {"notes": []}}
    captured: dict[str, object] = {}

    def capture(content, *args, **kwargs):  # type: ignore[no-untyped-def]
        captured["content"] = content
        return "item"

    with patch.object(stub, "_safe_store_with_edrr_phase", side_effect=capture):
        stub._persist_context_snapshot(Phase.EXPAND)

    stub._preserved_context["EXPAND"]["notes"].append("later")
    assert captured["content"] != stub._preserved_context
    assert captured["content"]["EXPAND"]["notes"] == []


def test_persist_context_snapshot_ignores_empty() -> None:
    """ReqID: N/A"""

    stub = StubPersistence(memory_manager=MagicMock())
    stub._preserved_context = {}
    with patch.object(stub, "_safe_store_with_edrr_phase") as store:
        stub._persist_context_snapshot(Phase.EXPAND)
    store.assert_not_called()
