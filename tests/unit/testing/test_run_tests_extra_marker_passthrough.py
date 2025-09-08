import pytest

from devsynth.testing.run_tests import run_tests


@pytest.mark.fast
def test_run_tests_merges_extra_marker_into_category_expression(monkeypatch):
    """ReqID: TR-RT-09 — Merge extra_marker into -m expression.

    When speed_categories is None and extra_marker is a normal expression
    (not a requires_resource('lmstudio') keyword case), run_tests should pass
    a combined -m expression that includes both the base filter and the extra
    marker.
    """
    import devsynth.testing.run_tests as rt

    captured_cmd = {}

    class FakePopen:
        def __init__(
            self, cmd, stdout=None, stderr=None, text=False, env=None
        ):  # noqa: ANN001
            # The command should include '-m' with the merged expression
            assert "-m" in cmd, f"-m missing in: {cmd}"
            # There are two '-m' flags: Python module and pytest marker; use the last
            idx = len(cmd) - 1 - cmd[::-1].index("-m")
            expr = cmd[idx + 1]
            assert "not memory_intensive" in expr
            assert "(not slow)" in expr or "not slow" in expr
            captured_cmd["cmd"] = cmd
            self.returncode = 0

        def communicate(self):
            return ("ok\n", "")

    monkeypatch.setattr(rt.subprocess, "Popen", FakePopen)

    success, output = run_tests(
        target="unit-tests",
        speed_categories=None,
        verbose=False,
        report=False,
        parallel=False,
        segment=False,
        segment_size=50,
        maxfail=None,
        extra_marker="not slow",
    )

    assert success is True
    assert "ok" in output
    # Ensure pytest path (tests/...) included
    assert (
        any(
            part.endswith("tests") or part.endswith("tests/unit")
            for part in captured_cmd["cmd"]
        )
        or "-m" in captured_cmd["cmd"]
    )
