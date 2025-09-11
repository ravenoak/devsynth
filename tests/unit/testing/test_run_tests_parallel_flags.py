import pytest

from devsynth.testing.run_tests import run_tests


@pytest.mark.fast
def test_run_tests_parallel_adds_no_cov_and_n_auto(monkeypatch):
    """ReqID: RUN-TESTS-PARALLEL-1

    When parallel=True and no explicit node ids are collected (single-pass branch),
    run_tests should include '-n auto' and '--no-cov' in the pytest command.
    """

    import devsynth.testing.run_tests as rt

    # We won't validate the collection step here; the single-pass branch does not
    # pre-collect node ids when speed_categories is None.

    class FakePopen:
        def __init__(
            self, cmd, stdout=None, stderr=None, text=False, env=None
        ):  # noqa: ANN001
            # Assert parallel-related flags are present
            assert "-n" in cmd and "auto" in cmd, f"parallel flags missing in: {cmd}"
            assert "--no-cov" in cmd, f"--no-cov missing in: {cmd}"
            self.returncode = 0

        def communicate(self):
            return ("ok\n", "")

    monkeypatch.setattr(rt.subprocess, "Popen", FakePopen)

    success, output = run_tests(
        target="unit-tests",
        speed_categories=None,  # triggers non-collection single-pass branch
        verbose=False,
        report=False,
        parallel=True,
        segment=False,
        segment_size=50,
        maxfail=None,
        extra_marker=None,
    )

    assert success is True
    assert "ok" in output or output == ""
