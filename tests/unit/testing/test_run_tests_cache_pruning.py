import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

import devsynth.testing.run_tests as rt
from devsynth.testing.run_tests import COLLECTION_CACHE_DIR, collect_tests_with_cache


@pytest.mark.fast
def test_prunes_nonexistent_paths_and_uses_cache(tmp_path, monkeypatch):
    """ReqID: CACHE-PRUNE-1"""
    # Prepare a fake cache with a nonexistent test path and an existent one
    os.makedirs(COLLECTION_CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(COLLECTION_CACHE_DIR, "unit-tests_all_tests.json")
    existent = "tests/unit/test_example.py::test_ok"
    nonexistent = "tests/unit/test_deleted.py::test_gone"
    # Ensure the existent path exists on filesystem for the pruning check
    exist_dir = Path("tests/unit")
    exist_dir.mkdir(parents=True, exist_ok=True)
    exist_file = exist_dir / "test_example.py"
    if not exist_file.exists():
        exist_file.write_text(
            "import pytest\n\n@pytest.mark.fast\ndef test_ok():\n    assert True\n"
        )

    cache_payload = {
        "timestamp": "2099-01-01T00:00:00",
        "tests": [existent, nonexistent],
        "fingerprint": {
            "latest_mtime": 0.0,
            "category_expr": "not memory_intensive",
            "test_path": "tests/",
            "node_set_hash": 123,
        },
    }
    with open(cache_file, "w") as f:
        json.dump(cache_payload, f)

    # Monkeypatch TTL to be huge so cache would be used if fingerprint matches
    monkeypatch.setenv("DEVSYNTH_COLLECTION_CACHE_TTL_SECONDS", "999999")

    def fake_run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        timeout=None,
        cwd=None,
        env=None,
    ):  # noqa: ANN001
        """Return the cached node ids without invoking pytest."""

        assert "--collect-only" in cmd, cmd
        return SimpleNamespace(
            returncode=0,
            stdout="\n".join([existent, nonexistent]),
            stderr="",
        )

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    # Force fingerprint mismatch by changing latest_mtime via
    # monkeypatching os.path.getmtime
    original_getmtime = os.path.getmtime

    def fake_getmtime(path):
        return 1.0

    monkeypatch.setattr(os.path, "getmtime", fake_getmtime)

    # Now call collection; it should regenerate and prune the nonexistent path
    out = collect_tests_with_cache(target="all-tests", speed_category=None)
    assert existent in out
    assert all(nonexistent != nid for nid in out)

    # Cleanup: restore getmtime
    monkeypatch.setattr(os.path, "getmtime", original_getmtime)
