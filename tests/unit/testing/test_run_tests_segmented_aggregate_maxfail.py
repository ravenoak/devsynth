from types import SimpleNamespace

import pytest

import devsynth.testing.run_tests as rt
from devsynth.testing.run_tests import run_tests


@pytest.mark.fast
@pytest.mark.requires_resource("codebase")
def test_segmented_aggregate_tips_command_includes_maxfail(monkeypatch) -> None:
    """
    ReqID: RT-11 — When segmented mode runs and any batch fails, the aggregated
    troubleshooting tips are generated using a command that includes --maxfail
    if maxfail was provided.
    """

    collected_ids = "tests/unit/sample_test.py::test_a\n"

    def fake_run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        timeout=None,
        cwd=None,
        env=None,
    ):  # noqa: ANN001
        # collection phase returns one node id (ensures one batch)
        return SimpleNamespace(returncode=0, stdout=collected_ids, stderr="")

    class FailingBatch:
        def __init__(
            self, cmd, stdout=None, stderr=None, text=False, env=None
        ):  # noqa: ANN001
            # Simulate a failing batch
            self.returncode = 1

        def communicate(self) -> tuple[str, str]:
            return ("", "boom")

    captured = {}

    def fake_failure_tips(returncode, cmd):  # noqa: ANN001
        # Capture the command used to generate tips for later assertion
        captured["cmd"] = cmd
        return "\nTroubleshooting tips: ...\n"

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
    monkeypatch.setattr(rt.subprocess, "Popen", FailingBatch)
    monkeypatch.setattr(rt, "_failure_tips", fake_failure_tips)

    success, output = run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=False,
        report=False,
        parallel=False,
        segment=True,
        segment_size=5,
        maxfail=2,
        extra_marker=None,
    )

    assert success is False
    assert "Troubleshooting tips" in output
    # Ensure --maxfail=2 was included in the aggregate cmd, not just batch cmd
    assert any(
        isinstance(arg, str) and arg.startswith("--maxfail=") and arg.endswith("2")
        for arg in captured.get("cmd", [])
    ), f"--maxfail not propagated in aggregate cmd: {captured}"
