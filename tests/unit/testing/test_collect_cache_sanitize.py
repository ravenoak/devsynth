import json
import os
from pathlib import Path

import pytest

from devsynth.testing.run_tests import (
    COLLECTION_CACHE_DIR,
    _sanitize_node_ids,
    collect_tests_with_cache,
)


@pytest.mark.fast
def test_sanitize_node_ids_strips_line_numbers_only_when_no_function_delimiter():
    raw = [
        "tests/unit/foo_test.py:123",  # should strip
        "tests/unit/bar_test.py::TestClass::test_method:456",  # should NOT strip
        "tests/unit/foo_test.py:123",  # duplicate; should dedupe
        "tests/unit/baz_test.py",  # keep
    ]
    cleaned = _sanitize_node_ids(raw)
    assert cleaned == [
        "tests/unit/foo_test.py",
        "tests/unit/bar_test.py::TestClass::test_method:456",
        "tests/unit/baz_test.py",
    ]


@pytest.mark.fast
def test_collect_tests_with_cache_prunes_nonexistent_and_caches(tmp_path, monkeypatch):
    # Create a fake tests directory with a simple structure
    tests_dir = tmp_path / "tests"
    unit_dir = tests_dir / "unit"
    unit_dir.mkdir(parents=True)
    # Create some dummy test files
    t1 = unit_dir / "test_a.py"
    t1.write_text("def test_a():\n    assert True\n")
    t2 = unit_dir / "test_b.py"
    t2.write_text("def test_b():\n    assert True\n")

    # Monkeypatch TARGET_PATHS lookup by pretending 'all-tests' maps to our tmp tests dir
    from devsynth.testing import run_tests as rt

    monkeypatch.setitem(rt.TARGET_PATHS, "all-tests", str(tests_dir))

    # Simulate pytest --collect-only -q output lines via subprocess.run
    class FakeProc:
        def __init__(self, stdout: str, returncode: int = 0, stderr: str = ""):
            self.stdout = stdout
            self.returncode = returncode
            self.stderr = stderr

    def fake_run(
        cmd, check=False, capture_output=True, text=True, timeout=None
    ):  # noqa: D401
        # Emit node ids including a non-existent file and a line-number suffix
        lines = [
            f"{t1}::test_a",
            f"{t2}:42",  # should be sanitized to path only then pruned check happens on path
            f"{tests_dir}/missing_test.py::test_missing",
        ]
        return FakeProc("\n".join(lines), 0, "")

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    # Ensure os.path.exists behaves normally but returns False for missing_test.py
    real_exists = os.path.exists

    def fake_exists(path):
        if str(path).endswith("missing_test.py"):
            return False
        return real_exists(path)

    monkeypatch.setattr(rt.os.path, "exists", fake_exists)

    # Point cache directory to tmp so we don't touch repo state
    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", str(tmp_path / ".cache"))

    out = collect_tests_with_cache("all-tests")
    # Should include t1 test node, and t2 sanitized to path exists so kept
    assert any(str(t1) in nid for nid in out)
    assert any(str(t2) in nid for nid in out)
    # Missing path should be pruned
    assert not any("missing_test.py" in nid for nid in out)

    # Verify cache file created with fingerprint keys
    cache_file = (
        Path(rt.COLLECTION_CACHE_DIR) / "all-tests_all_tests.json"
    )  # key format target_all
    # The actual filename format is f"{target}_{speed or 'all'}_tests.json"
    cache_file = Path(rt.COLLECTION_CACHE_DIR) / "all-tests_all_tests.json"
    # Adjust to actual naming
    cache_file = (
        Path(rt.COLLECTION_CACHE_DIR) / "all-tests_all_tests.json"
    )  # placeholder
    # Let's just locate any .json created in cache dir for robustness
    cache_dir = Path(rt.COLLECTION_CACHE_DIR)
    json_files = list(cache_dir.glob("*.json"))
    assert json_files, "expected a cache json file to be created"
    data = json.loads(json_files[0].read_text())
    assert "fingerprint" in data and "tests" in data
    assert isinstance(data["tests"], list)
