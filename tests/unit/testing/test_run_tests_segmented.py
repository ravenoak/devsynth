from types import SimpleNamespace
from typing import assert_type

import pytest

from devsynth.testing.run_tests import run_tests

from .run_tests_test_utils import build_batch_metadata


@pytest.mark.fast
@pytest.mark.requires_resource("codebase")
def test_run_tests_segmented_batches_execute(monkeypatch):
    """ReqID: RUN-TESTS-SEGMENTED-1

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
    def fake_run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        timeout=None,
        cwd=None,
        env=None,
    ):  # noqa: ANN001
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


@pytest.mark.fast
def test_run_tests_segmented_honors_keyword_filter(monkeypatch, tmp_path):
    """ReqID: RUN-TESTS-SEGMENTED-2 — Keyword filter applies during segmented runs."""

    tests_dir = tmp_path / "keyword"
    tests_dir.mkdir()
    (tests_dir / "test_one.py").write_text("def test_one():\n    assert True\n")
    (tests_dir / "test_two.py").write_text("def test_two():\n    assert True\n")

    import devsynth.testing.run_tests as rt

    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tests_dir))
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    collect_calls: list[list[str]] = []

    class FakeCollectProc:
        def __init__(self, stdout: str) -> None:
            self.stdout = stdout
            self.stderr = ""
            self.returncode = 0

    def fake_run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        timeout=None,
        cwd=None,
        env=None,
    ):
        collect_calls.append(cmd[:])
        assert "-k" in cmd, "keyword filter should be applied during collection"
        return FakeCollectProc(
            "\n".join(["test_one.py::test_one", "test_two.py::test_two"])
        )

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    batch_cmds: list[list[str]] = []

    class FakeBatchProcess:
        def __init__(
            self, cmd, stdout=None, stderr=None, text=False, env=None
        ):  # noqa: ANN001
            batch_cmds.append(cmd[:])
            self.returncode = 0
            self._stdout = "ok\n"
            self._stderr = ""

        def communicate(self):
            return self._stdout, self._stderr

    monkeypatch.setattr(rt.subprocess, "Popen", FakeBatchProcess)

    success, output = run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=False,
        report=False,
        parallel=False,
        segment=True,
        segment_size=1,
        maxfail=None,
        extra_marker="requires_resource('lmstudio')",
    )

    assert success is True
    assert any("-k" in cmd for cmd in collect_calls)
    assert len(batch_cmds) == 2
    assert all(
        len(
            [
                part
                for part in cmd
                if part.endswith("::test_one") or part.endswith("::test_two")
            ]
        )
        == 1
        for cmd in batch_cmds
    )
    assert "ok" in output


@pytest.mark.fast
def test_run_segmented_tests_stop_after_maxfail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: RUN-TESTS-SEGMENTED-8 — Stop remaining batches when maxfail is set."""

    import devsynth.testing.run_tests as rt

    seen_batches: list[list[str]] = []

    def fake_run_single_test_batch(
        config: rt.SingleBatchRequest,
    ) -> rt.BatchExecutionResult:
        assert_type(config, rt.SingleBatchRequest)
        node_ids = list(config.node_ids)
        seen_batches.append(node_ids)
        if len(seen_batches) > 1:
            pytest.fail("maxfail should stop additional segments")
        command = ["python-stop", *node_ids]
        return (
            False,
            "segment failed",
            build_batch_metadata(
                "batch-stop-1",
                command=command,
                returncode=1,
            ),
        )

    monkeypatch.setattr(rt, "_run_single_test_batch", fake_run_single_test_batch)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    request = rt.SegmentedRunRequest(
        target="unit-tests",
        speed_categories=("fast",),
        marker_expr="fast and not memory_intensive",
        node_ids=(
            "tests/unit/test_alpha.py::test_one",
            "tests/unit/test_beta.py::test_two",
        ),
        verbose=False,
        report=False,
        parallel=False,
        segment_size=1,
        maxfail=1,
        keyword_filter=None,
        env={},
    )

    success, output, metadata = rt._run_segmented_tests(request)

    assert seen_batches == [["tests/unit/test_alpha.py::test_one"]]
    assert success is False
    assert "segment failed" in output
    assert_type(metadata, rt.SegmentedRunMetadata)
    assert metadata["metadata_id"].startswith("segmented-")
    assert metadata["commands"] == [
        ["python-stop", "tests/unit/test_alpha.py::test_one"]
    ]
    assert metadata["segments"][0]["metadata_id"] == "batch-stop-1"
    assert list(metadata["segments"][0]["command"]) == metadata["commands"][0]
