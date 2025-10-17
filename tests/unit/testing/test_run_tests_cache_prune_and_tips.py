import json
import os
from types import SimpleNamespace

import pytest

from devsynth.testing.run_tests import (
    _failure_tips,
    collect_tests_with_cache,
)


@pytest.mark.fast
def test_failure_tips_contains_suggestions():
    tips = _failure_tips(2, ["python", "-m", "pytest", "-q"])
    assert "Pytest exited with code 2" in tips
    # A couple of representative suggestions
    assert "--smoke --speed=fast --no-parallel --maxfail=1" in tips
    assert "devsynth doctor" in tips
    assert "segment-size=50" in tips


@pytest.mark.fast
def test_collect_tests_with_cache_prunes_nonexistent_and_caches(tmp_path, monkeypatch):
    # Direct cache into a temp directory
    import devsynth.testing.run_tests as rt

    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", str(tmp_path / "cache"))

    # Simulate pytest --collect-only output with one non-existent and one existent file
    existing = "tests/unit/synthetic_test_file.py::test_ok"
    missing = "tests/unit/missing_test_file.py::test_missing"

    stdout = f"{missing}\n{existing}\n"

    def fake_run(cmd, check=False, capture_output=True, text=True, timeout=None, cwd=None, env=None):  # noqa: ANN001
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    # Make os.path.exists return True only for the existing path part
    real_exists = os.path.exists

    def fake_exists(path):  # noqa: ANN001
        if isinstance(path, str) and path.startswith(
            "tests/unit/synthetic_test_file.py"
        ):
            return True
        if isinstance(path, str) and path.startswith("tests/unit/missing_test_file.py"):
            return False
        return real_exists(path)

    monkeypatch.setattr(rt.os.path, "exists", fake_exists)

    results = collect_tests_with_cache(target="unit-tests", speed_category=None)
    assert existing in results
    assert all(missing not in r for r in results)

    # Verify cache file written contains only the pruned list
    cache_key = "unit-tests_all"
    cache_file = tmp_path / "cache" / f"{cache_key}_tests.json"
    assert cache_file.exists()
    data = json.loads(cache_file.read_text())
    assert data["tests"] == results
