from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

import devsynth.testing.run_tests as rt


@pytest.mark.fast
def test_collect_tests_with_cache_respects_ttl_expiry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ReqID: CTC-01 — TTL expiry invalidates stale cache entries."""

    tests_dir = tmp_path / "suite_ttl"
    tests_dir.mkdir()
    node = tests_dir / "test_ttl.py"
    node.write_text("def test_ttl():\n    assert True\n")

    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tests_dir))
    cache_dir = tmp_path / ".cache_ttl"
    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", str(cache_dir))
    monkeypatch.setattr(rt.os.path, "getmtime", lambda path: 42.0)
    monkeypatch.setattr(rt, "COLLECTION_CACHE_TTL_SECONDS", 0)

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / "unit-tests_fast_tests.json"
    payload = {
        "timestamp": (datetime.now() - timedelta(seconds=5)).isoformat(),
        "tests": [f"{node}::test_ttl"],
        "fingerprint": {
            "latest_mtime": 42.0,
            "category_expr": "fast and not memory_intensive",
            "test_path": str(tests_dir),
            "node_set_hash": 1,
        },
    }
    cache_file.write_text(json.dumps(payload))

    calls: list[list[str]] = []

    def fake_run(cmd, check=False, capture_output=True, text=True, timeout=None, cwd=None, env=None):  # noqa: ANN001
        calls.append(cmd)
        return SimpleNamespace(
            returncode=0,
            stdout=f"{node}::test_ttl\n",
            stderr="",
        )

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    result = rt.collect_tests_with_cache("unit-tests", "fast")

    assert result == [f"{node}::test_ttl"]
    assert len(calls) == 1
    updated = json.loads(cache_file.read_text())
    assert updated["fingerprint"]["latest_mtime"] == 42.0


@pytest.mark.fast
def test_collect_tests_with_cache_regenerates_on_fingerprint_mismatch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ReqID: CTC-02 — Fingerprint mismatch forces a fresh collection."""

    tests_dir = tmp_path / "suite_fingerprint"
    tests_dir.mkdir()
    node = tests_dir / "test_fp.py"
    node.write_text("def test_fp():\n    assert True\n")

    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tests_dir))
    cache_dir = tmp_path / ".cache_fp"
    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", str(cache_dir))
    cache_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(rt.os.path, "getmtime", lambda path: 321.0)
    monkeypatch.setattr(rt, "COLLECTION_CACHE_TTL_SECONDS", 3600)

    cache_file = cache_dir / "unit-tests_fast_tests.json"
    payload = {
        "timestamp": datetime.now().isoformat(),
        "tests": [f"{node}::test_fp"],
        "fingerprint": {
            "latest_mtime": 111.0,
            "category_expr": "fast and not memory_intensive",
            "test_path": str(tests_dir),
            "node_set_hash": 5,
        },
    }
    cache_file.write_text(json.dumps(payload))

    calls: list[list[str]] = []

    def fake_run(cmd, check=False, capture_output=True, text=True, timeout=None, cwd=None, env=None):  # noqa: ANN001
        calls.append(cmd)
        return SimpleNamespace(
            returncode=0,
            stdout=f"{node}::test_fp\n",
            stderr="",
        )

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    result = rt.collect_tests_with_cache("unit-tests", "fast")

    assert result == [f"{node}::test_fp"]
    assert len(calls) == 1
    updated = json.loads(cache_file.read_text())
    assert updated["fingerprint"]["latest_mtime"] == 321.0


@pytest.mark.fast
def test_collect_tests_with_cache_falls_back_to_cache_when_collection_empty(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ReqID: CTC-03 — Empty collections trigger fallback to pruned cache."""

    tests_dir = tmp_path / "suite_fallback"
    tests_dir.mkdir()
    keep = tests_dir / "test_keep.py"
    keep.write_text("def test_keep():\n    assert True\n")

    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tests_dir))
    cache_dir = tmp_path / ".cache_fb"
    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", str(cache_dir))
    monkeypatch.setattr(rt, "COLLECTION_CACHE_TTL_SECONDS", 0)
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_file = cache_dir / "unit-tests_all_tests.json"
    payload = {
        "timestamp": (datetime.now() - timedelta(seconds=10)).isoformat(),
        "tests": [
            f"{keep}::test_ok",
            f"{tests_dir / 'test_missing.py'}::test_missing",
        ],
        "fingerprint": {
            "latest_mtime": 10.0,
            "category_expr": "not memory_intensive",
            "test_path": str(tests_dir),
            "node_set_hash": 10,
        },
    }
    cache_file.write_text(json.dumps(payload))

    calls: list[list[str]] = []

    def fake_run(cmd, check=False, capture_output=True, text=True, timeout=None, cwd=None, env=None):  # noqa: ANN001
        calls.append(cmd)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    real_exists = rt.os.path.exists

    def fake_exists(path: str) -> bool:
        if path == str(keep):
            return True
        if path == str(tests_dir / "test_missing.py"):
            return False
        if path == str(cache_file):
            return True
        return real_exists(path)

    monkeypatch.setattr(rt.os.path, "exists", fake_exists)

    result = rt.collect_tests_with_cache("unit-tests", None)

    assert result == [f"{keep}::test_ok"]
    assert len(calls) == 2


@pytest.mark.fast
def test_collect_tests_with_cache_synthesizes_and_caches_node_ids(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ReqID: CTC-04 — Synthesized node list persists to cache when empty."""

    tests_dir = tmp_path / "suite_synth"
    tests_dir.mkdir(parents=True)
    file_a = tests_dir / "test_alpha.py"
    file_a.write_text("def test_alpha():\n    assert True\n")
    nested = tests_dir / "nested"
    nested.mkdir()
    file_b = nested / "test_beta.py"
    file_b.write_text("def test_beta():\n    assert True\n")

    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tests_dir))
    cache_dir = tmp_path / ".cache_synth"
    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", str(cache_dir))

    def fake_run(cmd, check=False, capture_output=True, text=True, timeout=None, cwd=None, env=None):  # noqa: ANN001
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    result = rt.collect_tests_with_cache("unit-tests", None)

    expected = {str(file_a), str(file_b)}
    assert set(result) == expected

    cache_file = Path(rt.COLLECTION_CACHE_DIR) / "unit-tests_all_tests.json"
    cache_data = json.loads(cache_file.read_text())
    assert set(cache_data["tests"]) == expected
