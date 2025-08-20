import pytest

from devsynth.testing.run_tests import TARGET_PATHS, run_tests


@pytest.mark.fast
def run_tests_completes_without_xdist_assertions(tmp_path, monkeypatch):
    test_file = tmp_path / "test_dummy.py"
    monkeypatch.setitem(TARGET_PATHS, "unit-tests", str(tmp_path))
    success, output = run_tests("unit-tests", ["fast"], parallel=True)
    assert success
    assert "INTERNALERROR" not in output
