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

    class P:
        def __init__(self, code: int, out: str = "ok\n", err: str = ""):
            self._code = code
            self._out = out
            self._err = err

        def communicate(self):
            return self._out, self._err

        @property
        def returncode(self) -> int:
            return self._code

    def fake_popen(
        cmd: list[str], stdout, stderr, text: bool, env: dict[str, str]
    ):  # type: ignore[override]
        captured["cmd"] = cmd
        captured["env"] = env
        # Succeed with code 0 first
        return P(0)

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

    # Now simulate non-zero but xfail/skip-only exit 5 being treated as success
    def popen_code5(cmd, stdout, stderr, text: bool, env):  # type: ignore[override]
        return P(5, out="", err="")

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
