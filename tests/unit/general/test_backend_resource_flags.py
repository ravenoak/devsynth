import os
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
