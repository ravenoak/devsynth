import json
from datetime import datetime, timedelta

import pytest

from devsynth.testing.run_tests import collect_tests_with_cache


@pytest.mark.fast
@pytest.mark.requires_resource("codebase")
def test_cache_uses_fresh_cache_without_subprocess_call(tmp_path, monkeypatch):
    """ReqID: CACHE-TTL-1"""
    # Arrange isolated tests dir and cache dir
    tests_dir = tmp_path / "isolated_tests_fresh"
    tests_dir.mkdir(parents=True, exist_ok=True)
    t1 = tests_dir / "test_alpha.py"
    # File existence matters for pruning; create it
    t1.write_text(
        "import pytest\n\n@pytest.mark.fast\ndef test_ok():\n    assert True\n"
    )

    # Redirect module globals
    import devsynth.testing.run_tests as rt

    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tests_dir) + "/")
    cache_dir = tmp_path / ".cache"
    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", str(cache_dir))

    # Stable mtime for fingerprint match
    monkeypatch.setattr(rt.os.path, "getmtime", lambda p: 123.456)

    # Prepare a fresh cache file that should be reused
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_key = "unit-tests_fast"
    cache_file = cache_dir / f"{cache_key}_tests.json"
    payload = {
        "timestamp": datetime.now().isoformat(),  # fresh
        "tests": [str(t1) + "::test_ok"],
        "fingerprint": {
            "latest_mtime": 123.456,
            "category_expr": "fast and not memory_intensive",
            "test_path": str(tests_dir) + "/",
            "node_set_hash": 111,
        },
    }
    cache_file.write_text(json.dumps(payload))

    # If subprocess.run is called, fail the test (cache should be used)
    def forbid_run(*args, **kwargs):  # pragma: no cover - should not be hit
        raise AssertionError("subprocess.run should not be called for fresh cache")

    monkeypatch.setattr(rt.subprocess, "run", forbid_run)

    # Act
    out = collect_tests_with_cache("unit-tests", "fast")

    # Assert: we got the cached list, and our node id is present
    assert any("test_alpha.py::test_ok" in nid for nid in out)


@pytest.mark.fast
@pytest.mark.requires_resource("codebase")
def test_cache_ttl_expired_triggers_subprocess_and_refresh(tmp_path, monkeypatch):
    """ReqID: CACHE-TTL-2"""
    # Arrange isolated tests dir and cache dir
    tests_dir = tmp_path / "isolated_tests_ttl"
    tests_dir.mkdir(parents=True, exist_ok=True)
    t1 = tests_dir / "test_beta.py"
    t1.write_text(
        "import pytest\n\n@pytest.mark.fast\ndef test_beta():\n    assert True\n"
    )

    import devsynth.testing.run_tests as rt

    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tests_dir) + "/")
    cache_dir = tmp_path / ".cache"
    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", str(cache_dir))

    # Keep fingerprint matching except TTL
    monkeypatch.setattr(rt.os.path, "getmtime", lambda p: 999.0)

    # Expire quickly: TTL = 1 second
    monkeypatch.setenv("DEVSYNTH_COLLECTION_CACHE_TTL_SECONDS", "1")
    # Re-import TTL constant by reloading module-level var
    # Note: the module reads TTL at import; our code in run_tests.py guards
    # ValueError and sets default.
    # For simplicity we won't force re-import. collect_tests_with_cache reads
    # the env only at import time for TTL, but it uses the module-level int
    # COLLECTION_CACHE_TTL_SECONDS.
    # We'll monkeypatch that directly for this test.
    monkeypatch.setattr(rt, "COLLECTION_CACHE_TTL_SECONDS", 1)

    # Prepare an old cache file whose timestamp is older than TTL
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_key = "unit-tests_fast"
    cache_file = cache_dir / f"{cache_key}_tests.json"
    old_time = (datetime.now() - timedelta(seconds=5)).isoformat()
    payload = {
        "timestamp": old_time,
        "tests": [str(t1) + "::test_beta"],
        "fingerprint": {
            "latest_mtime": 999.0,
            "category_expr": "fast and not memory_intensive",
            "test_path": str(tests_dir) + "/",
            "node_set_hash": 222,
        },
    }
    cache_file.write_text(json.dumps(payload))

    # Track subprocess invocations and emit a predictable collection
    calls = {"count": 0}

    class FakeProc:
        def __init__(self, stdout: str, returncode: int = 0, stderr: str = ""):
            self.stdout = stdout
            self.returncode = returncode
            self.stderr = stderr

    def fake_run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        timeout=None,
        cwd=None,
        env=None,
    ):
        calls["count"] += 1
        lines = [f"{t1}::test_beta"]
        return FakeProc("\n".join(lines), 0, "")

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    # Act: TTL expired so it should call subprocess and refresh cache
    out = collect_tests_with_cache("unit-tests", "fast")

    # Assert
    assert calls["count"] == 1
    assert any("test_beta.py::test_beta" in nid for nid in out)

    # Cache should now be updated with a newer timestamp
    new_data = json.loads(cache_file.read_text())
    assert datetime.fromisoformat(new_data["timestamp"]) >= datetime.fromisoformat(
        old_time
    )
    assert new_data["fingerprint"]["latest_mtime"] == 999.0
    assert new_data["fingerprint"]["category_expr"] == "fast and not memory_intensive"
    assert new_data["fingerprint"]["test_path"] == str(tests_dir) + "/"
