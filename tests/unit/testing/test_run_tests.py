from typing import Any

import pytest

from devsynth.testing import run_tests as rt


@pytest.mark.fast
def test_sanitize_node_ids_strips_line_numbers_without_function_delimiter():
    """ReqID: FR-11.2 — _sanitize_node_ids drops line numbers when no '::'."""
    raw = [
        "tests/unit/test_example.py:12",  # should strip :12
        "tests/unit/test_example.py::TestClass::test_method:45",  # has ::, keep :45
        "tests/unit/test_example.py::test_func",  # keep as-is
        "tests/unit/test_example.py:12",  # duplicate after sanitization, should dedupe
    ]
    out = rt._sanitize_node_ids(raw)
    assert out == [
        "tests/unit/test_example.py",
        "tests/unit/test_example.py::TestClass::test_method:45",
        "tests/unit/test_example.py::test_func",
    ]


@pytest.mark.fast
def test_failure_tips_contains_key_guidance_lines():
    """ReqID: FR-11.2 — _failure_tips lists common guidance knobs."""
    cmd = ["python", "-m", "pytest", "tests/unit"]
    tips = rt._failure_tips(1, cmd)
    # Starts with a summary line and contains several actionable hints
    assert "Pytest exited with code 1" in tips
    assert "--smoke" in tips
    assert "--segment-size=50" in tips
    assert "--maxfail=1" in tips
    assert "--no-parallel" in tips
    assert "--report" in tips


class _DummyCompleted:
    def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0) -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


class _DummyPopen:
    def __init__(
        self, expected_cmds: list[list[str]], rc_sequence: list[int] | None = None
    ):
        self._expected_cmds = expected_cmds
        self._seen: list[list[str]] = []
        self._i = 0
        self._rc_seq = rc_sequence or []

    def __call__(
        self,
        cmd: list[str],
        stdout: Any = None,
        stderr: Any = None,
        text: bool = True,
        env: dict[str, str] | None = None,
    ):
        # Record calls and return a handle with communicate()
        self._seen.append(cmd)
        idx = self._i
        self._i += 1
        rc = self._rc_seq[idx] if idx < len(self._rc_seq) else 0

        class _Handle:
            def __init__(self, rc: int) -> None:
                self.returncode = rc

            def communicate(self) -> tuple[str, str]:
                return ("", "")

        return _Handle(rc)

    @property
    def seen(self) -> list[list[str]]:
        return self._seen


@pytest.mark.fast
def test_run_tests_keyword_filter_no_matches(monkeypatch, tmp_path):
    """ReqID: FR-11.2 — Keyword path handles empty collection gracefully."""
    # Ensure test path exists to satisfy chdir logic
    tests_dir = tmp_path / "tests" / "unit"
    tests_dir.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)

    # Patch target path mapping to our tmp tests dir for unit-tests
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tests_dir))

    # Mock subprocess.run for collection to return no node ids
    def fake_run(
        cmd,
        check=False,
        capture_output=False,
        text=False,
        timeout=None,
        cwd=None,
        env=None,
    ):
        # Simulate --collect-only output with no matching lines
        return _DummyCompleted(stdout="", stderr="", returncode=0)

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    ok, output = rt.run_tests(
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
    assert ok is True
    assert "No tests matched" in output


@pytest.mark.fast
def test_run_tests_segment_batches(monkeypatch, tmp_path):
    """ReqID: FR-11.2 — Segmentation batches spawn multiple Popen runs."""
    # Create a fake tests dir and map target to it
    tests_dir = tmp_path / "tests" / "unit"
    tests_dir.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tests_dir))

    # Prepare collected node ids (5 tests => 3 batches with size 2)
    collected = [
        "tests/unit/test_a.py::test_1",
        "tests/unit/test_a.py::test_2",
        "tests/unit/test_b.py::test_3",
        "tests/unit/test_b.py::test_4",
        "tests/unit/test_c.py::test_5",
    ]

    def fake_run(
        cmd,
        check=False,
        capture_output=False,
        text=False,
        timeout=None,
        cwd=None,
        env=None,
    ):
        # Collection command returns the node ids in stdout, one per line
        if "--collect-only" in cmd:
            return _DummyCompleted(stdout="\n".join(collected), stderr="", returncode=0)
        return _DummyCompleted(stdout="", stderr="", returncode=0)

    dummy_popen = _DummyPopen(expected_cmds=[], rc_sequence=[0, 0, 0])

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
    monkeypatch.setattr(rt.subprocess, "Popen", dummy_popen)

    ok, output = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=False,
        report=False,
        parallel=False,
        segment=True,
        segment_size=2,
        maxfail=None,
        extra_marker=None,
    )

    assert ok is True
    # Ensure we spawned multiple batch runs. Expect 3 Popen calls for 5 tests at size 2
    assert len(dummy_popen.seen) == 3
    # Each command should include python -m pytest and our test node ids appended
    assert all(
        cmd[:3] == [rt.sys.executable, "-m", "pytest"] for cmd in dummy_popen.seen
    )


@pytest.mark.fast
def test_collect_tests_with_cache_writes_cache_and_sanitizes(monkeypatch, tmp_path):
    """ReqID: FR-11.2 — Collection cache stores sanitized node ids."""
    tests_dir = tmp_path / "tests"
    (tests_dir / "unit").mkdir(parents=True)
    # Create dummy test files to satisfy synthesized fallback if needed
    (tests_dir / "unit" / "test_x.py").write_text("\n")
    monkeypatch.chdir(tmp_path)

    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tests_dir / "unit"))

    # First run: provide some noisy output with line numbers and duplicates
    noisy = [
        "tests/unit/test_x.py:10",
        "tests/unit/test_x.py::test_ok",
        "tests/unit/test_x.py:10",  # duplicate
    ]

    def fake_run(
        cmd,
        check=False,
        capture_output=False,
        text=False,
        timeout=None,
        cwd=None,
        env=None,
    ):
        return _DummyCompleted(stdout="\n".join(noisy), stderr="", returncode=0)

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    out = rt.collect_tests_with_cache("unit-tests", "fast")
    # Sanitized and deduped: line numbers removed when no '::'
    assert out[0] == "tests/unit/test_x.py"
    assert any("::test_ok" in x for x in out)

    # Ensure cache file exists
    cache_dir = tmp_path / rt.COLLECTION_CACHE_DIR
    cache_files = list(cache_dir.glob("*_tests.json"))
    assert cache_files, "expected a cache file to be written"
