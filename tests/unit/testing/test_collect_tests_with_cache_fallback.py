import os
from types import SimpleNamespace

import pytest

from devsynth.testing.run_tests import collect_tests_with_cache


@pytest.mark.fast
def test_collect_uses_cached_and_prunes_when_collection_empty(monkeypatch, tmp_path):
    """ReqID: TR-RT-03 — Use cache and prune non-existent paths when empty."""
    # Redirect cache dir
    import devsynth.testing.run_tests as rt

    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", str(tmp_path))

    # Build the exact filename expected by collect_tests_with_cache
    expected_cache = tmp_path / "unit-tests_all_tests.json"
    expected_cache.write_text(
        "{\n"
        '  "timestamp": "2025-01-01T00:00:00",\n'
        '  "tests": [\n'
        '    "tests/unit/test_exists.py::test_ok",\n'
        '    "tests/unit/missing_test.py::test_missing"\n'
        "  ],\n"
        '  "fingerprint": {\n'
        '    "latest_mtime": 0.0,\n'
        '    "category_expr": "not memory_intensive",\n'
        '    "test_path": "tests/unit/"\n'
        "  }\n"
        "}\n"
    )

    # Mock subprocess.run to return empty stdout for both initial and fallback
    # collection invocations
    def fake_run(cmd, check=False, capture_output=False, text=False, timeout=None, cwd=None, env=None):
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    # Pretend tests/unit/ is a directory
    monkeypatch.setattr(
        rt.os.path,
        "isdir",
        lambda p: True if p.endswith("tests/unit/") else os.path.isdir(p),
    )

    # os.path.exists should be True only for the real test path part we want to keep
    def fake_exists(path: str) -> bool:
        if path.endswith("tests/unit/test_exists.py"):
            return True
        if path.endswith("tests/unit/missing_test.py"):
            return False
        # Allow cache file and temp dir checks
        if str(path).startswith(str(tmp_path)):
            return True
        return os.path.exists(path)

    monkeypatch.setattr(rt.os.path, "exists", fake_exists)

    out = collect_tests_with_cache(target="unit-tests", speed_category=None)

    # Should prune missing_test and keep only existing one from cache
    assert out == ["tests/unit/test_exists.py::test_ok"]


@pytest.mark.fast
def test_collect_falls_back_to_unfiltered_and_returns_sanitized_ids(
    monkeypatch, tmp_path
):
    """ReqID: TR-RT-04 — Fallback to unfiltered and sanitize node ids."""
    import devsynth.testing.run_tests as rt

    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", str(tmp_path))

    # First filtered collection is empty
    def run_filtered(cmd, check=False, capture_output=False, text=False):
        # Heuristic: presence of "-m" in cmd implies filtered
        if "-m" in cmd and "addopts=" in cmd:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        # Fallback unfiltered returns some node ids with and without line numbers
        stdout = "\n".join(
            [
                "tests/unit/test_sample.py::TestX::test_a",
                "tests/unit/test_other.py:12",  # should be sanitized to drop :12
            ]
        )
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

    monkeypatch.setattr(rt.subprocess, "run", run_filtered)

    # Pretend tests/unit/ is a directory and paths exist for pruning
    monkeypatch.setattr(
        rt.os.path,
        "isdir",
        lambda p: True if p.endswith("tests/unit/") else os.path.isdir(p),
    )
    monkeypatch.setattr(
        rt.os.path,
        "exists",
        lambda p: (
            True
            if (
                p.endswith("tests/unit/test_sample.py")
                or p.endswith("tests/unit/test_other.py")
            )
            else os.path.exists(p)
        ),
    )

    out = collect_tests_with_cache(target="unit-tests", speed_category=None)

    assert out == [
        "tests/unit/test_sample.py::TestX::test_a",
        "tests/unit/test_other.py",
    ]
