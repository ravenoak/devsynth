import json
from types import SimpleNamespace
from typing import Any

import pytest

import devsynth.testing.run_tests as rt


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch):
    # ensure env isolation relevant to runner
    keys = [
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
        "PYTEST_ADDOPTS",
        "DEVSYNTH_COLLECTION_CACHE_TTL_SECONDS",
    ]
    for k in keys:
        monkeypatch.delenv(k, raising=False)
    yield
    for k in keys:
        monkeypatch.delenv(k, raising=False)


@pytest.mark.fast
def test_sanitize_node_ids_dedup_and_strip_line_numbers():
    """ReqID: RTM-01 — _sanitize_node_ids de-duplicates and strips trailing line
    numbers except after '::'."""
    # has line numbers and duplicates and function ids
    raw = [
        "tests/unit/foo/test_a.py:12",
        "tests/unit/foo/test_a.py:12",  # duplicate
        "tests/unit/foo/test_b.py::TestB::test_x",
        "tests/unit/foo/test_b.py::TestB::test_x",  # duplicate keeps one
        "tests/unit/bar/test_c.py:99",
    ]
    out = rt._sanitize_node_ids(raw)
    assert out == [
        "tests/unit/foo/test_a.py",
        "tests/unit/foo/test_b.py::TestB::test_x",
        "tests/unit/bar/test_c.py",
    ]


@pytest.mark.fast
def test_collect_tests_with_cache_uses_cache_and_respects_ttl(
    monkeypatch: pytest.MonkeyPatch, tmp_path
):
    """ReqID: RTM-02 — collect_tests_with_cache caches and reuses results
    respecting TTL and fingerprint."""
    # Point TARGET_PATHS to tmp tests dir
    tests_dir = tmp_path / "tests" / "unit"
    tests_dir.mkdir(parents=True)
    (tests_dir / "test_sample.py").write_text("def test_ok():\n    assert True\n")

    # Monkeypatch TARGET_PATHS and subprocess to avoid invoking real pytest
    monkeypatch.setattr(
        rt, "TARGET_PATHS", {"unit-tests": str(tests_dir), "all-tests": str(tests_dir)}
    )

    class DummyProc:
        def __init__(self, out: str):
            self.stdout = out
            self.returncode = 0

    def fake_run(
        cmd: list[str], check: bool, capture_output: bool, text: bool
    ):  # type: ignore[override]
        assert "--collect-only" in cmd
        # emulate -q output: one per line
        return DummyProc(out=f"{tests_dir}/test_sample.py\n")

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    # Speed None path
    ids1 = rt.collect_tests_with_cache("unit-tests", speed_category=None)
    assert ids1 == [str(tests_dir / "test_sample.py")]

    # Create cache by calling again with same params; replace subprocess to
    # raise if called
    def fail_run(
        *a: Any, **k: Any
    ):  # pragma: no cover - would indicate cache miss unexpectedly
        raise AssertionError("subprocess.run should not be called when cache is warm")

    monkeypatch.setattr(rt.subprocess, "run", fail_run)

    ids2 = rt.collect_tests_with_cache("unit-tests", speed_category=None)
    assert ids2 == ids1  # served from cache


@pytest.mark.fast
def test_run_tests_translates_args_and_handles_return_codes(
    monkeypatch: pytest.MonkeyPatch, tmp_path
):
    """ReqID: RTM-03 — run_tests translates args, treats code 0/5 as success,
    and omits -n when parallel=False."""
    # Arrange base to avoid plugin interactions and filesystem writes
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_x.py").write_text("def test_one():\n    assert True\n")
    monkeypatch.setattr(
        rt, "TARGET_PATHS", {"unit-tests": str(tests_dir), "all-tests": str(tests_dir)}
    )

    # Capture the command built for the run path (no speed_categories provided)
    captured = {"cmd": None, "env": None}

    class CollectResult:
        def __init__(self, out: str) -> None:
            self.stdout = out
            self.stderr = ""
            self.returncode = 0

    def fake_run(
        cmd: list[str],
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> CollectResult:  # type: ignore[override]
        assert "--collect-only" in cmd
        return CollectResult(f"{tests_dir}/test_x.py::test_one\n")

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    class P:
        def __init__(self, cmd: list[str], code: int, out: str = "ok\n", err: str = ""):
            self.args = cmd
            self._code = code
            self._out = out
            self._err = err

        def communicate(self, *_args: Any, **_kwargs: Any):
            return self._out, self._err

        @property
        def returncode(self) -> int:
            return self._code

        def __enter__(self) -> "P":
            return self

        def __exit__(
            self,
            _exc_type: Any,
            _exc: Any,
            _tb: Any,
        ) -> bool:
            return False

        def kill(self) -> None:  # pragma: no cover - subprocess.run compatibility
            pass

        def wait(self) -> int:  # pragma: no cover - subprocess.run compatibility
            return self._code

        def poll(self) -> int:  # pragma: no cover - subprocess.run compatibility
            return self._code

    def fake_popen(
        cmd: list[str],
        stdout,
        stderr,
        text: bool,
        env: dict[str, str] | None = None,
    ):  # type: ignore[override]
        captured["cmd"] = cmd
        captured["env"] = env
        # Succeed with code 0 first
        return P(cmd, 0)

    monkeypatch.setattr(rt.subprocess, "Popen", fake_popen)

    ok, output = rt.run_tests(
        target="unit-tests", speed_categories=["fast"], parallel=False
    )
    assert ok is True
    assert "ok" in output or output == ""  # output may be empty in our fake
    # Command should include pytest module runner and our test path followed by
    # node ids; since we passed a speed, it should collect then run
    cmd = captured["cmd"]
    assert cmd is not None
    assert cmd[0:3] == [rt.sys.executable, "-m", "pytest"]
    # parallel=False ensures '-n auto' is not present
    assert "-n" not in cmd
    assert f"--cov={rt.COVERAGE_TARGET}" in cmd
    assert f"--cov-report=json:{rt.COVERAGE_JSON_PATH}" in cmd
    assert f"--cov-report=html:{rt.COVERAGE_HTML_DIR}" in cmd
    assert "--cov-append" in cmd

    # Now simulate non-zero but xfail/skip-only exit 5 being treated as success
    def popen_code5(
        cmd,
        stdout,
        stderr,
        text: bool,
        env: dict[str, str] | None = None,
    ):  # type: ignore[override]
        return P(cmd, 5, out="", err="")

    monkeypatch.setattr(rt.subprocess, "Popen", popen_code5)
    ok5, _ = rt.run_tests(
        target="unit-tests", speed_categories=["fast"], parallel=False
    )
    assert ok5 is True


@pytest.mark.fast
def test_run_tests_keyword_filter_for_extra_marker_lmstudio(
    monkeypatch: pytest.MonkeyPatch, tmp_path
):
    """ReqID: RTM-04 — extra_marker 'requires_resource("lmstudio")' uses
    keyword filter and early success on no matches."""
    # Arrange: ensure keyword narrowing path is exercised with no matches ->
    # early success
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    monkeypatch.setattr(
        rt, "TARGET_PATHS", {"unit-tests": str(tests_dir), "all-tests": str(tests_dir)}
    )

    class Dummy:
        def __init__(self, stdout: str, returncode: int = 0):
            self.stdout = stdout
            self.returncode = returncode

    def fake_run(
        cmd, check: bool, capture_output: bool, text: bool
    ):  # type: ignore[override]
        # '--collect-only' path with '-k lmstudio' produces no items
        assert "--collect-only" in cmd
        return Dummy(stdout="")

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    ok, msg = rt.run_tests(
        target="unit-tests",
        speed_categories=None,
        extra_marker="requires_resource('lmstudio')",
    )
    assert ok is True
    assert "No tests matched" in msg


@pytest.mark.fast
def test_run_tests_handles_popen_exception_without_speed_filters(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """ReqID: RTM-05 — run_tests surfaces subprocess errors with guidance."""

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    monkeypatch.setattr(
        rt, "TARGET_PATHS", {"unit-tests": str(tests_dir), "all-tests": str(tests_dir)}
    )

    # ``run_tests`` should not perform collection when no speed categories are
    # provided. Guard against unexpected subprocess.run usage.
    def fail_run(*_args: Any, **_kwargs: Any) -> None:  # pragma: no cover - safety
        raise AssertionError("subprocess.run should not be invoked in this branch")

    monkeypatch.setattr(rt.subprocess, "run", fail_run)

    captured: dict[str, list[str]] = {}

    def boom_popen(
        cmd: list[str],
        stdout: Any = None,
        stderr: Any = None,
        text: bool = True,
        env: dict[str, str] | None = None,
    ) -> Any:  # pragma: no cover - behavior exercised via exception path
        captured["cmd"] = cmd
        raise RuntimeError("intentional popen failure")

    monkeypatch.setattr(rt.subprocess, "Popen", boom_popen)

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
    assert "intentional popen failure" in output
    assert "Pytest exited with code -1" in output
    assert "Troubleshooting tips" in output
    assert captured["cmd"][0:3] == [rt.sys.executable, "-m", "pytest"]


@pytest.mark.fast
def test_collect_unknown_target_uses_all_tests_path(monkeypatch, tmp_path):
    """ReqID: RTM-06 — Unknown target falls back to all-tests mapping."""

    tests_dir = tmp_path / "some_tests"
    tests_dir.mkdir()
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", str(cache_dir))
    monkeypatch.setattr(rt, "TARGET_PATHS", {"all-tests": str(tests_dir)})

    observed: list[list[str]] = []

    def fake_run(
        cmd,
        check=False,
        capture_output=False,
        text=False,
        timeout=None,
        cwd=None,
        env=None,
    ):  # noqa: ANN001
        observed.append(cmd[:])
        return SimpleNamespace(
            stdout="test_sample.py::test_ok\n",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    original_isdir = rt.os.path.isdir

    def fake_isdir(path: str) -> bool:
        if path == str(tests_dir):
            return False
        return original_isdir(path)

    monkeypatch.setattr(rt.os.path, "isdir", fake_isdir)

    original_exists = rt.os.path.exists

    def fake_exists(path: str) -> bool:
        if path == "test_sample.py":
            return True
        return original_exists(path)

    monkeypatch.setattr(rt.os.path, "exists", fake_exists)

    result = rt.collect_tests_with_cache("custom-target", speed_category=None)

    assert result == ["test_sample.py::test_ok"]
    assert observed, "expected subprocess.run to be invoked"
    assert observed[0][3] == str(tests_dir)


@pytest.mark.fast
def test_enforce_coverage_threshold_exit_and_return(tmp_path):
    """ReqID: RTM-05 — Coverage helper returns percent and exits on failure."""

    cov_file = tmp_path / "coverage.json"
    cov_file.write_text(json.dumps({"totals": {"percent_covered": 95.25}}))
    percent = rt.enforce_coverage_threshold(
        coverage_file=cov_file, exit_on_failure=False
    )
    assert percent == pytest.approx(95.25)

    cov_file.write_text(json.dumps({"totals": {"percent_covered": 81.7}}))
    with pytest.raises(RuntimeError):
        rt.enforce_coverage_threshold(coverage_file=cov_file, exit_on_failure=False)

    with pytest.raises(SystemExit) as excinfo:
        rt.enforce_coverage_threshold(coverage_file=cov_file)
    assert excinfo.value.code == 1


@pytest.mark.fast
def test_failure_tips_includes_segmentation_guidance() -> None:
    """ReqID: RTM-06 — _failure_tips returns actionable suggestions."""

    cmd = ["python", "-m", "pytest", "tests/unit"]

    tips = rt._failure_tips(3, cmd)

    assert tips.startswith("\n") and tips.endswith("\n")
    assert "Pytest exited with code 3" in tips
    assert "Troubleshooting tips" in tips
    assert "Segment large suites to localize failures" in tips
    assert "devsynth run-tests --target unit-tests --speed=fast --segment" in tips


@pytest.mark.fast
def test_run_tests_segment_appends_aggregation_tips(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """ReqID: RTM-07 — Segmented failures append aggregate troubleshooting tips."""

    tests_dir = tmp_path / "segmented"
    tests_dir.mkdir()
    (tests_dir / "test_one.py").write_text("def test_one():\n    assert True\n")
    (tests_dir / "test_two.py").write_text("def test_two():\n    assert True\n")

    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tests_dir))
    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)

    class CollectProc:
        def __init__(self, out: str) -> None:
            self.stdout = out
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
    ):  # noqa: ANN001
        assert "--collect-only" in cmd
        stdout = "\n".join(["test_one.py::test_one", "test_two.py::test_two"])
        return CollectProc(stdout)

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    batch_calls: list[list[str]] = []

    class FakeBatchProcess:
        def __init__(
            self,
            cmd,
            stdout=None,
            stderr=None,
            text=False,
            env=None,
        ) -> None:  # noqa: ANN001
            batch_calls.append(cmd)
            self.args = cmd
            index = len(batch_calls) - 1
            if index == 0:
                self._stdout = "batch-1\n"
                self._stderr = ""
                self._returncode = 0
            else:
                self._stdout = "batch-2\n"
                self._stderr = "boom"
                self._returncode = 1

        def communicate(self):  # noqa: D401 - simple stub
            return self._stdout, self._stderr

        @property
        def returncode(self) -> int:
            return self._returncode

    monkeypatch.setattr(rt.subprocess, "Popen", FakeBatchProcess)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=False,
        report=False,
        parallel=False,
        segment=True,
        segment_size=1,
        maxfail=None,
        extra_marker=None,
    )

    assert success is False
    assert len(batch_calls) == 2

    expected_agg_cmd = [
        rt.sys.executable,
        "-m",
        "pytest",
        f"--cov={rt.COVERAGE_TARGET}",
        "--cov-report=term-missing",
        f"--cov-report=json:{rt.COVERAGE_JSON_PATH}",
        f"--cov-report=html:{rt.COVERAGE_HTML_DIR}",
        "--cov-append",
        str(tests_dir),
    ]
    aggregate_tip = rt._failure_tips(1, expected_agg_cmd)

    assert aggregate_tip in output


@pytest.mark.fast
def test_enforce_coverage_threshold_errors_on_missing_file(tmp_path):
    """ReqID: RTM-08 — Missing coverage file raises helpful errors."""

    cov_file = tmp_path / "missing.json"

    with pytest.raises(RuntimeError) as excinfo:
        rt.enforce_coverage_threshold(coverage_file=cov_file, exit_on_failure=False)
    assert "Coverage report not found" in str(excinfo.value)

    with pytest.raises(SystemExit):
        rt.enforce_coverage_threshold(coverage_file=cov_file)


@pytest.mark.fast
def test_enforce_coverage_threshold_errors_on_invalid_json(tmp_path):
    """ReqID: RTM-09 — Invalid JSON surfaces explicit diagnostics."""

    cov_file = tmp_path / "invalid.json"
    cov_file.write_text("{not json")

    with pytest.raises(RuntimeError) as excinfo:
        rt.enforce_coverage_threshold(coverage_file=cov_file, exit_on_failure=False)
    assert "invalid" in str(excinfo.value)

    with pytest.raises(SystemExit):
        rt.enforce_coverage_threshold(coverage_file=cov_file)
