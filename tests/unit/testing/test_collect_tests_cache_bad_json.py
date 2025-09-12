import json
import subprocess

import pytest

import devsynth.testing.run_tests as rt


@pytest.mark.fast
def test_collect_tests_with_cache_bad_json(tmp_path, monkeypatch):
    """Malformed cache file triggers regeneration.

    ReqID: N/A"""
    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", str(tmp_path))
    cache = tmp_path / "unit-tests_all_tests.json"
    cache.write_text("{bad json}")

    class Res:
        stdout = "tests/unit/sample_test.py::test_a\n"
        returncode = 0

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: Res())
    out = rt.collect_tests_with_cache("unit-tests", None)
    assert out == ["tests/unit/sample_test.py::test_a"]
    new_cache = json.loads(cache.read_text())
    assert new_cache["tests"] == out
