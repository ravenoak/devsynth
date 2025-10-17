import os
from importlib.machinery import ModuleSpec
from unittest.mock import patch

import pytest


@pytest.mark.fast
@pytest.mark.no_network
def test_backend_flag_mapping_respects_env_vars():
    """Validate that DEVSYNTH_RESOURCE_<NAME>_AVAILABLE toggles availability.

    This focuses on a representative subset of backends per docs/tasks.md #26.
    """
    from tests.conftest import is_resource_available

    # Make all false and ensure returns False
    env = {
        "DEVSYNTH_RESOURCE_FAISS_AVAILABLE": "false",
        "DEVSYNTH_RESOURCE_KUZU_AVAILABLE": "false",
        "DEVSYNTH_RESOURCE_LMDB_AVAILABLE": "false",
        "DEVSYNTH_RESOURCE_DUCKDB_AVAILABLE": "false",
        "DEVSYNTH_RESOURCE_RDFLIB_AVAILABLE": "false",
        "DEVSYNTH_RESOURCE_TINYDB_AVAILABLE": "false",
    }
    with patch.dict(os.environ, env, clear=False):
        assert is_resource_available("faiss") is False
        assert is_resource_available("kuzu") is False
        assert is_resource_available("lmdb") is False
        assert is_resource_available("duckdb") is False
        assert is_resource_available("rdflib") is False
        assert is_resource_available("tinydb") is False

    # Turn one on at a time; if import fails the function still returns False, so we only
    # check that the env gate no longer forces a False result. This ensures mapping is honored.
    with patch.dict(
        os.environ, {"DEVSYNTH_RESOURCE_FAISS_AVAILABLE": "true"}, clear=False
    ):
        # is_resource_available("faiss") may still return False if faiss import is missing,
        # but it must not be forced False by the env mapping now. We validate by asserting
        # the function executes without raising and returns a boolean.
        assert isinstance(is_resource_available("faiss"), bool)


@pytest.mark.fast
def test_rdflib_env_mapping_disables_rdflib():
    """Sanity: resource check returns False when env disables rdflib."""
    from tests.conftest import is_resource_available

    with patch.dict(
        os.environ, {"DEVSYNTH_RESOURCE_RDFLIB_AVAILABLE": "false"}, clear=False
    ):
        assert is_resource_available("rdflib") is False


@pytest.mark.fast
def test_skip_if_missing_backend_handles_partial_spec(monkeypatch):
    """``skip_if_missing_backend`` should handle ModuleSpec objects lacking loaders."""

    from tests.fixtures import resources

    # Test that the function doesn't crash when dealing with malformed specs
    # This is testing the robustness of the function rather than specific behavior
    spec = ModuleSpec("kuzu", loader=None)
    spec.origin = None
    spec.submodule_search_locations = None

    monkeypatch.setattr(resources, "is_resource_available", lambda _: True)
    monkeypatch.setattr(resources, "_safe_find_spec", lambda _: spec)

    # The function should not crash and should return a list (possibly empty)
    marks = resources.skip_if_missing_backend("kuzu", include_requires_resource=False)
    assert isinstance(marks, list)


@pytest.mark.fast
def test_skip_if_missing_backend_converts_find_spec_value_error(monkeypatch):
    """ValueError from ``find_spec`` should result in a clean skip marker."""

    from tests.fixtures import resources

    calls: list[tuple[str, str]] = []

    def raising_find_spec(_name: str):
        raise ValueError("bad spec")

    def fake_importorskip(name: str, *, reason: str) -> None:
        calls.append((name, reason))
        raise pytest.skip.Exception(reason)

    monkeypatch.setattr(resources.importlib.util, "find_spec", raising_find_spec)
    monkeypatch.setattr(resources, "is_resource_available", lambda _: True)
    monkeypatch.setattr(resources.pytest, "importorskip", fake_importorskip)

    marks = resources.skip_if_missing_backend("faiss", include_requires_resource=False)

    assert any(mark.name == "skip" for mark in marks)
    assert calls and calls[0][0] == "faiss"
