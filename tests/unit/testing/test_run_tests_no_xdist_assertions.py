import pytest

from devsynth.testing.run_tests import TARGET_PATHS, run_tests


@pytest.mark.fast
def test_run_tests_completes_without_xdist_assertions(tmp_path, monkeypatch):
    test_file = tmp_path / "test_dummy.py"
    test_file.write_text(
        "import pytest\n\n@pytest.mark.fast\ndef test_dummy():\n    assert True\n"
    )
    monkeypatch.setitem(TARGET_PATHS, "unit-tests", str(tmp_path))
    success, output = run_tests("unit-tests", ["fast"], parallel=True)
    assert success
    assert "INTERNALERROR" not in output
