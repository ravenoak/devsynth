from types import SimpleNamespace

import pytest

import devsynth.testing.run_tests as rt
from devsynth.testing.run_tests import TARGET_PATHS, run_tests


@pytest.mark.fast
def test_run_tests_completes_without_xdist_assertions(tmp_path, monkeypatch):
    """run_tests completes without INTERNALERROR when run in parallel. ReqID: FR-22"""
    test_file = tmp_path / "test_dummy.py"
    test_file.write_text(
        "import pytest\n\n@pytest.mark.fast\ndef test_ok():\n    assert True\n"
    )
    monkeypatch.setitem(TARGET_PATHS, "unit-tests", str(tmp_path))
    monkeypatch.setitem(rt.TARGET_PATHS, "all-tests", str(tmp_path))
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    def fake_collect(cmd, check=False, capture_output=True, text=True):  # noqa: ANN001
        assert "--collect-only" in cmd
        return SimpleNamespace(
            returncode=0,
            stdout=f"{test_file}::test_ok",
            stderr="",
        )

    class FakePopen:
        def __init__(
            self, cmd, stdout=None, stderr=None, text=True, env=None
        ):  # noqa: ANN001
            assert "-n" in cmd and "auto" in cmd
            self.returncode = 0
            self._stdout = "passed"
            self._stderr = ""

        def communicate(self):  # noqa: D401 - mimic subprocess API
            """Return deterministic stdout/stderr."""

            return self._stdout, self._stderr

    monkeypatch.setattr(rt.subprocess, "run", fake_collect)
    monkeypatch.setattr(rt.subprocess, "Popen", FakePopen)

    success, output = run_tests("unit-tests", ["fast"], parallel=True)
    assert success
    assert "INTERNALERROR" not in output
