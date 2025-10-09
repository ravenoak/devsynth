"""Targeted coverage tests for ``devsynth.testing.run_tests`` logic."""

from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from freezegun import freeze_time

import devsynth.testing.run_tests as rt
from tests._typing_utils import typed_freeze_time


@pytest.mark.fast
def test_sanitize_node_ids_strips_line_numbers_without_function_delimiter():
    """ReqID: FR-11.2 — _sanitize_node_ids drops line numbers when no '::'."""
    raw = [
        "tests/unit/test_example.py:12",  # should strip :12
        "tests/unit/test_example.py::TestClass::test_method:45",  # has ::, keep :45
        "tests/unit/test_example.py::test_func",  # keep as-is
        "tests/unit/test_example.py:12",  # duplicate after sanitization, should dedupe
    ]
    out = rt._sanitize_node_ids(raw)
    assert out == [
        "tests/unit/test_example.py",
        "tests/unit/test_example.py::TestClass::test_method:45",
        "tests/unit/test_example.py::test_func",
    ]


@pytest.mark.fast
def test_failure_tips_contains_key_guidance_lines():
    """ReqID: FR-11.2 — _failure_tips lists common guidance knobs."""
    cmd = ["python", "-m", "pytest", "tests/unit"]
    tips = rt._failure_tips(1, cmd)
    # Starts with a summary line and contains several actionable hints
    assert "Pytest exited with code 1" in tips
    assert "--smoke" in tips
    assert "--segment-size=50" in tips
    assert "--maxfail=1" in tips
    assert "--no-parallel" in tips
    assert "--report" in tips


@typed_freeze_time("2025-01-01")
@pytest.mark.fast
def test_collect_tests_with_cache_uses_cache(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ReqID: RUN-TESTS-COLL-1 — collect_tests_with_cache uses the cache."""
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    cache_dir = tmp_path / rt.COLLECTION_CACHE_DIR
    cache_dir.mkdir()
    cache_file = cache_dir / "unit-tests_fast_tests.json"
    cached_data = {
        "timestamp": "2025-01-01T00:00:00.000000",
        "tests": [os.path.join(str(tmp_path), "test_file.py")],
        "fingerprint": {
            "latest_mtime": 1.0,
            "category_expr": "fast and not memory_intensive",
            "test_path": str(tmp_path),
        },
    }
    with open(cache_file, "w") as f:
        json.dump(cached_data, f)

    (tmp_path / "test_file.py").write_text("def test_example(): pass")
    with (
        patch.object(rt.os.path, "getmtime", return_value=1.0),
        patch.object(rt.subprocess, "run") as mock_run,
        patch.object(rt, "COLLECTION_CACHE_TTL_SECONDS", 999999),
    ):
        tests = rt.collect_tests_with_cache("unit-tests", "fast")

        assert tests == [expected_path]
    mock_run.assert_not_called()


@typed_freeze_time("2025-01-02")
@pytest.mark.fast
def test_collect_tests_with_cache_regenerates_when_expired(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ReqID: RUN-TESTS-COLL-2 — collect_tests_with_cache regenerates when expired."""
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    cache_dir = tmp_path / rt.COLLECTION_CACHE_DIR
    cache_dir.mkdir()
    cache_file = cache_dir / "unit-tests_fast_tests.json"
    cached_data = {
        "timestamp": "2025-01-01T00:00:00.000000",
        "tests": [os.path.join(str(tmp_path), "test_file.py")],
        "fingerprint": {
            "latest_mtime": 0.5,
            "category_expr": "fast and not memory_intensive",
            "test_path": str(tmp_path),
        },
    }
    with open(cache_file, "w") as f:
        json.dump(cached_data, f)

    (tmp_path / "test_file.py").write_text("def test_example(): pass")
    with (
        patch.object(rt.os.path, "getmtime", return_value=1.0),
        patch.object(rt.subprocess, "run") as mock_run,
        patch.object(rt, "COLLECTION_CACHE_TTL_SECONDS", 999999),
    ):
        mock_run.return_value = SimpleNamespace(
            stdout=os.path.join(str(tmp_path), "new_test.py") + "\n",
            returncode=0,
            stderr="",
        )
        tests = rt.collect_tests_with_cache("unit-tests", "fast")

    assert tests == [os.path.join(tmp_path, "new_test.py")]
    mock_run.assert_called()


@typed_freeze_time("2025-01-01")
@pytest.mark.fast
def test_collect_tests_with_cache_miss(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ReqID: RUN-TESTS-COLL-3 — collect_tests_with_cache handles a cache miss."""
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    (tmp_path / "test_file.py").write_text("def test_example(): pass")

    with (
        patch.object(rt.os.path, "getmtime", return_value=1.0),
        patch.object(rt.subprocess, "run") as mock_run,
        patch.object(rt, "COLLECTION_CACHE_TTL_SECONDS", 999999),
    ):
        mock_run.return_value = SimpleNamespace(
            stdout=os.path.join(str(tmp_path), "test_file.py") + "\n",
            returncode=0,
            stderr="",
        )
        tests = rt.collect_tests_with_cache("unit-tests", "fast")

    assert tests == [os.path.join(tmp_path, "test_file.py")]
    mock_run.assert_called()


@typed_freeze_time("2025-01-01")
@pytest.mark.fast
def test_collect_tests_with_cache_invalidated_by_mtime(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ReqID: RUN-TESTS-COLL-4 — collect_tests_with_cache is invalidated by mtime."""
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    cache_dir = tmp_path / rt.COLLECTION_CACHE_DIR
    cache_dir.mkdir()
    cache_file = cache_dir / "unit-tests_fast_tests.json"
    cached_data = {
        "timestamp": "2025-01-01T00:00:00.000000",
        "tests": [os.path.join(str(tmp_path), "test_file.py")],
        "fingerprint": {
            "latest_mtime": 0.5,
            "category_expr": "fast and not memory_intensive",
            "test_path": str(tmp_path),
        },
    }
    with open(cache_file, "w") as f:
        json.dump(cached_data, f)

    (tmp_path / "test_file.py").write_text("def test_example(): pass")
    with (
        patch.object(rt.os.path, "getmtime", return_value=1.0),
        patch.object(rt.subprocess, "run") as mock_run,
        patch.object(rt, "COLLECTION_CACHE_TTL_SECONDS", 999999),
    ):
        mock_run.return_value = SimpleNamespace(
            stdout=os.path.join(str(tmp_path), "new_test.py") + "\n",
            returncode=0,
            stderr="",
        )
        with freeze_time("2025-01-02"):
            tests = rt.collect_tests_with_cache("unit-tests", "fast")

    assert tests == [os.path.join(tmp_path, "new_test.py")]
    mock_run.assert_called()


@typed_freeze_time("2025-01-01")
@pytest.mark.fast
def test_collect_tests_with_cache_invalidated_by_marker(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ReqID: RUN-TESTS-COLL-5 — collect_tests_with_cache is invalidated by marker."""
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    cache_dir = tmp_path / rt.COLLECTION_CACHE_DIR
    cache_dir.mkdir()
    cache_file = cache_dir / "unit-tests_fast_tests.json"
    cached_data = {
        "timestamp": "2025-01-01T00:00:00.000000",
        "tests": [os.path.join(str(tmp_path), "test_file.py")],
        "fingerprint": {
            "latest_mtime": 1.0,
            "category_expr": "fast and not memory_intensive",
            "test_path": str(tmp_path),
        },
    }
    with open(cache_file, "w") as f:
        json.dump(cached_data, f)

    (tmp_path / "test_file.py").write_text("def test_example(): pass")
    with (
        patch.object(rt.os.path, "getmtime", return_value=1.0),
        patch.object(rt.subprocess, "run") as mock_run,
        patch.object(rt, "COLLECTION_CACHE_TTL_SECONDS", 999999),
    ):
        mock_run.return_value = SimpleNamespace(
            stdout=os.path.join(str(tmp_path), "new_test.py") + "\n",
            returncode=0,
            stderr="",
        )
        with freeze_time("2025-01-01"):
            tests = rt.collect_tests_with_cache("unit-tests", "slow")

    assert tests == [os.path.join(tmp_path, "new_test.py")]
    mock_run.assert_called()
