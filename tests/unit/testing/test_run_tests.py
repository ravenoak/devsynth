# flake8: noqa: E501
import logging
from pathlib import Path
from typing import Any

import pytest

import devsynth.testing.run_tests as rt


@pytest.mark.fast
def test_run_tests_parallel_adds_xdist_and_no_cov(monkeypatch, tmp_path) -> None:
    """ReqID: FR-11.2 — Parallel mode adds xdist and disables coverage."""
    # Intercept Popen
    recorded: dict[str, Any] = {}

    class DummyProc:
        def __init__(self, args: list[str]) -> None:
            self.args = args
            self.returncode = 0

        def communicate(self) -> tuple[str, str]:
            return ("ok", "")

    def fake_popen(args, stdout=None, stderr=None, text=None, env=None):  # type: ignore[no-redef]
        recorded["args"] = list(args)
        recorded["env"] = dict(env or {})
        return DummyProc(list(args))

    monkeypatch.setattr(rt.subprocess, "Popen", fake_popen)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=None,
        verbose=False,
        report=False,
        parallel=True,
        segment=False,
        segment_size=50,
        maxfail=None,
    )

    assert success is True
    args = recorded["args"]
    # -n auto and --no-cov present for parallel path
    assert "-n" in args and "auto" in args
    assert "--no-cov" in args


@pytest.mark.fast
def test_run_tests_report_creates_dir_and_passes_html(monkeypatch, tmp_path) -> None:
    """ReqID: FR-11.2 — --report creates directory and passes --html to pytest."""
    # Intercept Popen to avoid running pytest
    captured = {"args": None}

    class DummyProc:
        def __init__(self, args: list[str]) -> None:
            self.returncode = 0

        def communicate(self) -> tuple[str, str]:
            return ("ok", "")

    def fake_popen(args, stdout=None, stderr=None, text=None, env=None):  # type: ignore[no-redef]
        captured["args"] = list(args)
        return DummyProc(list(args))

    monkeypatch.setattr(rt.subprocess, "Popen", fake_popen)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=None,
        verbose=True,
        report=True,
        parallel=False,
        segment=False,
        segment_size=50,
        maxfail=1,
    )

    assert success is True
    args = captured["args"] or []
    # Verbose should add -v; maxfail should be forwarded
    assert "-v" in args
    assert any(a.startswith("--maxfail=") and a.endswith("1") for a in args)
    html_args = [a for a in args if a.startswith("--html=")]
    assert html_args, "--html was not passed"
    report_path = Path(html_args[0].split("=", 1)[1])
    assert report_path.parent.exists()


@pytest.mark.fast
def test_keyword_filter_lmstudio(monkeypatch) -> None:
    """ReqID: FR-11.2 — keyword filter path with lmstudio marker executes collected IDs."""

    # Simulate collect-only returning two node ids
    def fake_run(cmd, check=False, capture_output=False, text=False):  # type: ignore[no-redef]
        class R:
            def __init__(self) -> None:
                self.returncode = 0
                self.stdout = "tests/unit/test_a.py::t1\n" "tests/unit/test_b.py::t2\n"
                self.stderr = ""

        return R()

    class DummyProc:
        def __init__(self, args: list[str]) -> None:
            self.returncode = 0

        def communicate(self) -> tuple[str, str]:
            return ("ok", "")

    def fake_popen(args, stdout=None, stderr=None, text=None, env=None):  # type: ignore[no-redef]
        return DummyProc(list(args))

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
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
        extra_marker="requires_resource('lmstudio')",
    )

    assert success is True
    # Output is the standard combined output; since we mocked, just ensure not an error
    assert "No tests matched" not in output


@pytest.mark.fast
def test_speed_categories_with_segmentation_batches(monkeypatch, tmp_path) -> None:
    """ReqID: FR-11.2 — segmentation batches are sized and executed correctly."""
    # Prepare a set of collected node ids via monkeypatching internal collection
    # We'll hook into subprocess.run used during collection to return 7 tests
    test_root = tmp_path / "tests" / "unit"
    test_root.mkdir(parents=True)
    f = test_root / "test_sample.py"
    f.write_text("""import pytest\n@pytest.mark.fast\ndef test_a(): pass\n""")

    node_ids = [f"{f}::test_{i}" for i in range(7)]

    def fake_run(cmd, check=False, capture_output=False, text=False):  # type: ignore[no-redef]
        class R:
            def __init__(self) -> None:
                self.returncode = 0
                self.stdout = "\n".join(node_ids) + "\n"
                self.stderr = ""

        return R()

    started_batches = []

    class DummyProc:
        def __init__(self, args: list[str]) -> None:
            self.args = args
            self.returncode = 0

        def communicate(self) -> tuple[str, str]:
            return ("ok", "")

    def fake_popen(args, stdout=None, stderr=None, text=None, env=None):  # type: ignore[no-redef]
        # Record batch sizes by counting test ids in args (everything ending with '::test_X')
        batch = [a for a in args if str(f) in a and "::" in a]
        if batch:
            started_batches.append(len(batch))
        return DummyProc(list(args))

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
    monkeypatch.setattr(rt.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(
        rt, "TARGET_PATHS", {"unit-tests": str(test_root), "all-tests": str(test_root)}
    )

    success, _ = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=False,
        report=False,
        parallel=False,
        segment=True,
        segment_size=3,
        maxfail=None,
    )

    assert success is True
    # Expect 3,3,1 batching across 7 items with size=3
    assert started_batches == [3, 3, 1]


@pytest.mark.fast
def test_collect_tests_with_cache_basic(monkeypatch, tmp_path) -> None:
    """ReqID: FR-11.2 — collection caches results and sanitizes node IDs."""
    # Ensure a temporary test tree
    root = tmp_path / "tests" / "unit"
    root.mkdir(parents=True)
    tfile = root / "test_x.py"
    tfile.write_text("def test_ok():\n    assert True\n")

    # Mock subprocess.run for collection
    def fake_run(cmd, check=False, capture_output=False, text=False):  # type: ignore[no-redef]
        class R:
            def __init__(self) -> None:
                self.returncode = 0
                # include a trailing :123 that should be sanitized when no '::' present
                self.stdout = f"{tfile}:123\n{tfile}::test_ok\n"
                self.stderr = ""

        return R()

    monkeypatch.setattr(
        rt, "TARGET_PATHS", {"unit-tests": str(root), "all-tests": str(root)}
    )
    monkeypatch.setenv("DEVSYNTH_COLLECTION_CACHE_TTL_SECONDS", "999999")
    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    ids = rt.collect_tests_with_cache("unit-tests", "fast")
    # Both entries should be present, with the first sanitized to drop :123
    assert any(str(tfile) == i for i in ids)
    assert any(f"{tfile}::test_ok" == i for i in ids)

    # Second call should hit cache; change the fake_run to raise to ensure cache is used
    def bad_run(cmd, check=False, capture_output=False, text=False):  # type: ignore[no-redef]
        raise AssertionError("should use cache")

    monkeypatch.setattr(rt.subprocess, "run", bad_run)
    ids2 = rt.collect_tests_with_cache("unit-tests", "fast")
    assert ids2 == ids


@pytest.mark.fast
def test_keyword_filter_no_matches_returns_success_message(monkeypatch) -> None:
    """ReqID: FR-11.2 — keyword filter with no matches returns success tip."""

    # Simulate collect-only returning no matches
    def fake_run(cmd, check=False, capture_output=False, text=False):  # type: ignore[no-redef]
        class R:
            def __init__(self) -> None:
                self.returncode = 0
                self.stdout = ""  # no items
                self.stderr = ""

        return R()

    class DummyProc:
        def __init__(self, args: list[str]) -> None:
            self.returncode = 0

        def communicate(self) -> tuple[str, str]:
            return ("ok", "")

    def fake_popen(args, stdout=None, stderr=None, text=None, env=None):  # type: ignore[no-redef]
        return DummyProc(list(args))

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
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
        extra_marker="requires_resource('lmstudio')",
    )

    assert success is True
    assert "No tests matched the provided filters." in output


@pytest.mark.fast
def test_collect_tests_with_cache_empty_then_synthesizes(monkeypatch, tmp_path) -> None:
    """ReqID: FR-11.2 — synthesizes file-based ids when collection returns empty."""
    # Build a tiny filesystem with one test file; initial collection simulates empty
    root = tmp_path / "tests" / "unit"
    root.mkdir(parents=True)
    tfile = root / "test_synth.py"
    tfile.write_text("def test_ok():\n    assert True\n")

    # First run returns empty; second fallback (without markers) also empty; synthesis should kick in
    calls = {"count": 0}

    def fake_run(cmd, check=False, capture_output=False, text=False):  # type: ignore[no-redef]
        class R:
            def __init__(self) -> None:
                self.returncode = 0
                self.stderr = ""
                calls["count"] += 1
                # First and second collection attempts yield no stdout
                self.stdout = ""

        return R()

    monkeypatch.setattr(
        rt, "TARGET_PATHS", {"unit-tests": str(root), "all-tests": str(root)}
    )
    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    ids = rt.collect_tests_with_cache("unit-tests", "fast")
    # With both collections empty, the function should synthesize from filesystem
    assert any(str(tfile) in nid for nid in ids)


@pytest.mark.fast
def test_segmentation_logs_progress_messages(monkeypatch, tmp_path, caplog) -> None:
    """ReqID: FR-11.2 — logs show batch progress for segmentation path."""
    # Prepare a set of collected node ids via monkeypatching internal collection
    test_root = tmp_path / "tests" / "unit"
    test_root.mkdir(parents=True)
    f = test_root / "test_sample.py"
    f.write_text("""import pytest\n@pytest.mark.fast\ndef test_a(): pass\n""")

    node_ids = [f"{f}::test_{i}" for i in range(7)]

    def fake_run(cmd, check=False, capture_output=False, text=False):  # type: ignore[no-redef]
        class R:
            def __init__(self) -> None:
                self.returncode = 0
                self.stdout = "\n".join(node_ids) + "\n"
                self.stderr = ""

        return R()

    class DummyProc:
        def __init__(self, args: list[str]) -> None:
            self.returncode = 0

        def communicate(self) -> tuple[str, str]:
            return ("ok", "")

    def fake_popen(args, stdout=None, stderr=None, text=None, env=None):  # type: ignore[no-redef]
        return DummyProc(list(args))

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
    monkeypatch.setattr(rt.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(
        rt, "TARGET_PATHS", {"unit-tests": str(test_root), "all-tests": str(test_root)}
    )

    # Capture INFO logs because segmentation progress uses logger.info
    with caplog.at_level(logging.INFO):
        success, _ = rt.run_tests(
            target="unit-tests",
            speed_categories=["fast"],
            verbose=True,  # ensure info level
            report=False,
            parallel=False,
            segment=True,
            segment_size=3,
            maxfail=None,
        )

    assert success is True
    # Expect messages about found tests and batches
    assert any(
        "Found 7 fast tests, running in batches of 3" in rec.message
        for rec in caplog.records
    )
    assert any("Running batch" in rec.message for rec in caplog.records)


@pytest.mark.fast
def test_segmentation_failing_batch_logs_tips_and_sets_failure(
    monkeypatch, tmp_path, caplog
) -> None:
    """ReqID: FR-11.2 — failing batch emits troubleshooting tips and returns failure."""
    # Arrange: create a fake test tree and collected node ids
    test_root = tmp_path / "tests" / "unit"
    test_root.mkdir(parents=True)
    f = test_root / "test_sample.py"
    f.write_text("""import pytest\n@pytest.mark.fast\ndef test_a(): pass\n""")

    node_ids = [f"{f}::test_{i}" for i in range(7)]

    # Collect-only returns our node_ids
    def fake_run(cmd, check=False, capture_output=False, text=False):  # type: ignore[no-redef]
        class R:
            def __init__(self) -> None:
                self.returncode = 0
                self.stdout = "\n".join(node_ids) + "\n"
                self.stderr = ""

        return R()

    # Popen simulates three batches with middle failing (non-zero return code)
    calls = {"count": 0}

    class DummyProc:
        def __init__(self, idx: int) -> None:
            # Batch 1 ok, Batch 2 fails, Batch 3 ok
            if idx == 1:
                self.returncode = 2
                self._stdout = ""
                self._stderr = "E failing\n"
            else:
                self.returncode = 0
                self._stdout = "ok\n"
                self._stderr = ""

        def communicate(self):  # type: ignore[no-redef]
            return (self._stdout, self._stderr)

    def fake_popen(args, stdout=None, stderr=None, text=None, env=None):  # type: ignore[no-redef]
        idx = calls["count"]
        calls["count"] += 1
        return DummyProc(idx)

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
    monkeypatch.setattr(rt.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(
        rt, "TARGET_PATHS", {"unit-tests": str(test_root), "all-tests": str(test_root)}
    )

    with caplog.at_level(logging.INFO):
        success, output = rt.run_tests(
            target="unit-tests",
            speed_categories=["fast"],
            verbose=True,
            report=False,
            parallel=False,
            segment=True,
            segment_size=3,
            maxfail=None,
        )

    # Assert: overall success should be False due to failing batch
    assert success is False
    # Tips should be logged and included in output
    assert "Troubleshooting tips:" in output
    assert any("Pytest exited with code" in rec.message for rec in caplog.records)
