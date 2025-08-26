import pytest

from devsynth.testing.run_tests import TARGET_PATHS, run_tests


@pytest.mark.fast
def test_failure_tips_include_common_flags(tmp_path, monkeypatch):
    """ReqID: FR-59 Ensure failure tips include common flags examples.

    We create a minimal failing test and assert that the output contains
    actionable hints for --smoke, --segment/--segment-size, --maxfail,
    --no-parallel, and --report.
    """
    test_file = tmp_path / "test_fails.py"
    test_file.write_text(
        """
import pytest

@pytest.mark.fast
def test_will_fail():
    assert False
"""
    )
    # Point unit-tests target to our tmp_path
    monkeypatch.setitem(TARGET_PATHS, "unit-tests", str(tmp_path))

    success, output = run_tests("unit-tests", ["fast"], parallel=False)

    assert not success, "Run should fail to trigger tips"
    # Check that enriched tips are present
    assert "--smoke" in output
    assert "--segment-size" in output
    assert "--maxfail" in output
    assert "--no-parallel" in output
    assert "--report" in output
