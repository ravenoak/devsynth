import os

import pytest

import devsynth.testing.run_tests as rt


@pytest.mark.fast
@pytest.mark.test_metrics
def test_coverage_artifacts_created_when_no_tests(tmp_path, monkeypatch):
    """ReqID: run-tests-coverage-no-tests"""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    monkeypatch.setitem(rt.TARGET_PATHS, "dummy-tests", str(empty_dir))
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        success, _ = rt.run_tests("dummy-tests", ["fast"], report=False, parallel=False)
    finally:
        os.chdir(cwd)
    assert success
    assert (tmp_path / "htmlcov" / "index.html").exists()
    assert (tmp_path / "coverage.json").exists()
