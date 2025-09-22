from types import SimpleNamespace

import pytest

import devsynth.testing.run_tests as rt
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

    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    def fake_collect(cmd, check=False, capture_output=True, text=True):  # noqa: ANN001
        assert "--collect-only" in cmd
        return SimpleNamespace(
            returncode=0,
            stdout=f"{test_file}::test_will_fail",
            stderr="",
        )

    class FakePopen:
        def __init__(self, cmd, stdout=None, stderr=None, text=True, env=None):  # noqa: ANN001
            self.cmd = list(cmd)
            self.returncode = 1
            self._stdout = ""
            self._stderr = "FAIL Required test coverage of 90% not reached."

        def communicate(self):  # noqa: D401 - mimic subprocess signature
            """Return predetermined stdout/stderr."""

            return self._stdout, self._stderr

    monkeypatch.setattr(rt.subprocess, "run", fake_collect)
    monkeypatch.setattr(rt.subprocess, "Popen", FakePopen)

    success, output = run_tests("unit-tests", ["fast"], parallel=False)

    assert not success, "Run should fail to trigger tips"
    # Check that enriched tips are present
    assert "--smoke" in output
    assert "--segment-size" in output
    assert "--maxfail" in output
    assert "--no-parallel" in output
    assert "--report" in output
