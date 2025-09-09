import subprocess
import types

import pytest

# Speed marker discipline
pytestmark = pytest.mark.fast


def test_collect_tests_with_cache_synthesizes_when_empty(monkeypatch, tmp_path):
    """ReqID: TR-RT-02 — Synthesize minimal list when collection is empty.

    When both primary and fallback collections return no node ids and no cache exists,
    collect_tests_with_cache should synthesize a minimal file list by scanning the
    filesystem under the target path for test_*.py files.
    """
    # Arrange: create an isolated temporary test tree
    test_root = tmp_path / "tests" / "unit"
    test_root.mkdir(parents=True)
    dummy = test_root / "test_dummy.py"
    dummy.write_text("def test_ok():\n    assert True\n")

    # Import module under test
    from devsynth.testing import run_tests as rt

    # Point the target mapping to our isolated test directory
    old_target = rt.TARGET_PATHS.get("unit-tests")
    rt.TARGET_PATHS["unit-tests"] = str(test_root)

    # Ensure cwd is the temp directory so the cache dir is local and empty
    monkeypatch.chdir(tmp_path)

    # Monkeypatch subprocess.run to simulate empty collection outputs for both
    # the primary and fallback collectors.
    def _fake_run(
        cmd, check=False, capture_output=True, text=True
    ):  # type: ignore[override]
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", _fake_run)

    # Act: call collect with speed_category=None to exercise the synthesize path
    result = rt.collect_tests_with_cache("unit-tests", None)

    # Cleanup mapping even if assertions fail
    rt.TARGET_PATHS["unit-tests"] = old_target

    # Assert: synthesized list contains our dummy test file path
    assert str(dummy) in result
    # Also verify the cache file was created under the local cache dir
    cache_dir = tmp_path / rt.COLLECTION_CACHE_DIR
    assert cache_dir.exists()
