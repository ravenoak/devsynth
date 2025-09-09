import importlib
import os
import sys
from types import ModuleType

import pytest

# Speed discipline
pytestmark = pytest.mark.fast


def reload_run_tests_with_env(key: str, value: str) -> ModuleType:
    # Ensure a clean reload to pick up env initialization at import time
    if "devsynth.testing.run_tests" in sys.modules:
        del sys.modules["devsynth.testing.run_tests"]
    os.environ[key] = value
    import devsynth.testing.run_tests as rt  # type: ignore

    importlib.reload(rt)
    return rt


def test_bad_ttl_env_falls_back_to_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """ReqID: TR-RT-05 — Malformed TTL falls back to default."""
    # Set a malformed TTL so int() conversion would fail; module should
    # fall back to 3600
    monkeypatch.delenv("DEVSYNTH_COLLECTION_CACHE_TTL_SECONDS", raising=False)
    rt = reload_run_tests_with_env(
        "DEVSYNTH_COLLECTION_CACHE_TTL_SECONDS", "not-an-int"
    )
    assert rt.COLLECTION_CACHE_TTL_SECONDS == 3600


def test_sanitize_node_ids_preserves_function_qualifier_and_strips_line_numbers() -> (
    None
):
    """ReqID: TR-RT-06 — Sanitize node ids: strip line nums without '::',
    preserve with '::'."""
    # When '::' is present, do not strip trailing :<digits> (line numbers are
    # part of id after function)
    # When '::' is absent, strip trailing :<digits> which are not meaningful as
    # selectors
    from devsynth.testing.run_tests import (  # import after reload tests above
        _sanitize_node_ids,
    )

    raw = [
        "tests/unit/foo/test_example.py::TestClass::test_it:42",
        "tests/unit/foo/test_example.py:99",  # no '::' => strip :99
        "tests/unit/foo/test_example.py::test_other",  # keep as-is
        "tests/unit/foo/test_example.py::test_other",  # duplicate => dedupe
    ]
    cleaned = _sanitize_node_ids(raw)

    assert cleaned == [
        "tests/unit/foo/test_example.py::TestClass::test_it:42",  # preserved
        "tests/unit/foo/test_example.py",  # stripped line number
        "tests/unit/foo/test_example.py::test_other",  # preserved
    ]
