import pytest

import devsynth.testing.run_tests as rt


@pytest.mark.fast
def test_keyword_filter_no_matches_returns_success(monkeypatch) -> None:
    """ReqID: RT-01 — keyword filter with no matches returns success and message."""

    # Simulate collect-only returning no matching node ids under keyword filter
    def fake_run(
        cmd,  # noqa: ANN001
        check: bool = False,
        capture_output: bool = False,
        text: bool = False,
    ):  # type: ignore[no-redef]
        class R:
            def __init__(self) -> None:
                self.returncode = 0
                # nothing that matches the node id regex
                self.stdout = "\n"
                self.stderr = ""

        return R()

    # Ensure Popen is not invoked if there are no node ids
    def fail_popen(*args, **kwargs):  # type: ignore[no-redef]
        pytest.fail("Popen should not be called when no node ids match")

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
    monkeypatch.setattr(rt.subprocess, "Popen", fail_popen)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=None,
        verbose=False,
        report=False,
        parallel=False,
        segment=False,
        segment_size=50,
        maxfail=None,
        extra_marker="requires_resource('lmstudio')",
    )

    assert success is True
    assert "No tests matched the provided filters." in output


@pytest.mark.fast
def test_failure_tips_appended_on_nonzero_return(monkeypatch) -> None:
    """ReqID: RT-02 — non-zero exit appends troubleshooting tips."""

    # Make the simple '-m not memory_intensive' path run and return a non-zero code
    class DummyProc:
        def __init__(self) -> None:
            self.returncode = 2

        def communicate(self) -> tuple[str, str]:
            return ("", "boom")

    def fake_popen(
        args,  # noqa: ANN001
        stdout=None,  # noqa: ANN001
        stderr=None,  # noqa: ANN001
        text=None,  # noqa: ANN001
        env=None,  # noqa: ANN001
    ):  # type: ignore[no-redef]
        return DummyProc()

    monkeypatch.setattr(rt.subprocess, "Popen", fake_popen)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=None,
        verbose=False,
        report=False,
        parallel=False,
        segment=False,
        segment_size=50,
        maxfail=None,
        extra_marker=None,
    )

    assert success is False
    # Failure tips should be appended to the output
    assert "Pytest exited with code" in output
    assert "Troubleshooting tips:" in output
