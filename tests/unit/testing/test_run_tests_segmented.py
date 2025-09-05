import itertools
from types import SimpleNamespace

import pytest

from devsynth.testing.run_tests import run_tests


@pytest.mark.fast
@pytest.mark.requires_resource("codebase")
def test_run_tests_segmented_batches_execute(monkeypatch):
    """
    Cover the segmented execution branch: when speed_categories are provided and
    segment=True, run_tests should execute tests in batches via Popen.
    """
    # Simulate collection of two node IDs for a given speed category
    collected_ids = (
        "tests/unit/module_a_test.py::test_a1\n"
        "tests/unit/module_b_test.py::test_b1\n"
    )

    import devsynth.testing.run_tests as rt

    # Fake subprocess.run to return our collected node ids
    def fake_run(cmd, check=False, capture_output=True, text=True):  # noqa: ANN001
        # Ensure --collect-only was requested for the marker-based collection
        assert "--collect-only" in cmd and "-q" in cmd
        return SimpleNamespace(returncode=0, stdout=collected_ids, stderr="")

    # Counter to verify batches executed
    calls = []

    class FakePopen:
        def __init__(
            self, cmd, stdout=None, stderr=None, text=False, env=None
        ):  # noqa: ANN001
            # The command should contain exactly one node id per batch
            node_args = [c for c in cmd if c.startswith("tests/") and "::" in c]
            assert (
                len(node_args) == 1
            ), f"expected single test node id per batch, got: {node_args}"
            calls.append(node_args[0])
            self.returncode = 0

        def communicate(self):
            return ("ok\n", "")

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
    monkeypatch.setattr(rt.subprocess, "Popen", FakePopen)

    success, output = run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=False,
        report=False,
        parallel=False,
        segment=True,
        segment_size=1,  # force 1 test per batch
        maxfail=None,
        extra_marker=None,
    )

    assert success is True
    # Two batches should have been invoked
    assert calls == [
        "tests/unit/module_a_test.py::test_a1",
        "tests/unit/module_b_test.py::test_b1",
    ]
    assert "ok" in output or output == ""
