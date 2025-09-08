from typing import Any

import pytest

from devsynth.testing.run_tests import collect_tests_with_cache


class _CP:
    def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


@pytest.mark.fast
def test_collect_behavior_tests_fallback_when_no_tests_ran(monkeypatch, tmp_path):
    """ReqID: TR-RT-01 — Behavior/integration fallback when no tests ran."""
    # Simulate the behavior/integration fallback branch when a speed_category is
    # provided and the initial collection yields "no tests ran". The function
    # should retry with a relaxed marker expression and return the second set of
    # collected node ids.

    calls: list[dict[str, Any]] = []

    def fake_run(
        cmd, check=False, capture_output=False, text=False
    ):  # type: ignore[no-untyped-def]
        # Record the call for assertions
        calls.append({"cmd": cmd[:]})
        joined = " ".join(cmd)
        if "--collect-only" in cmd and "-m" in cmd:
            # First path: the pre-check for behavior/integration when
            # speed_category is set
            if "tests/behavior/" in joined or cmd[-1] == ".":
                # Return a signal equivalent to no tests collected under this
                # filter
                return _CP(stdout="no tests ran\n", returncode=0)
        # The subsequent actual collect_cmd should run with either relaxed
        # marker or same path. Return a couple of synthetic node ids to be
        # sanitized.
        out = (
            "tests/behavior/test_fake.py::test_case\n"
            "tests/behavior/test_other.py::test_ok\n"
        )
        return _CP(stdout=out, returncode=0)

    monkeypatch.setattr("subprocess.run", fake_run)

    # Use a temporary cache dir so we don't affect the real project cache
    monkeypatch.setenv("DEVSYNTH_COLLECTION_CACHE_TTL_SECONDS", "1")
    # Force cache directory to tmp by changing CWD since function writes relative path
    monkeypatch.chdir(tmp_path)

    # Create a minimal behavior tests tree so pruning-by-existence keeps our ids
    (tmp_path / "tests" / "behavior").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tests" / "behavior" / "test_fake.py").write_text(
        "def test_case():\n    assert True\n"
    )
    (tmp_path / "tests" / "behavior" / "test_other.py").write_text(
        "def test_ok():\n    assert True\n"
    )

    result = collect_tests_with_cache(target="behavior-tests", speed_category="fast")

    # Ensure we received the synthetic ids from the second call
    assert any(x.endswith("test_fake.py::test_case") for x in result)
    assert any(x.endswith("test_other.py::test_ok") for x in result)

    # Verify that our check path was invoked and then the main collect path
    assert any("--collect-only" in c["cmd"] and "-m" in c["cmd"] for c in calls)
    assert len(result) == 2
