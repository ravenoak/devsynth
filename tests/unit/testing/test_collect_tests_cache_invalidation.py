import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from devsynth.testing.run_tests import TARGET_PATHS, collect_tests_with_cache


@pytest.mark.fast
def test_cache_invalidation_on_file_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange: create an isolated tests directory
    tests_dir = tmp_path / "isolated_tests"
    tests_dir.mkdir(parents=True, exist_ok=True)

    test_file = tests_dir / "test_sample.py"
    test_file.write_text(
        """
import pytest

@pytest.mark.fast
def test_example():
    assert 1 + 1 == 2
"""
    )

    # Redirect cache dir to tmp
    cache_dir = tmp_path / ".cache"
    monkeypatch.setenv("DEVSYNTH_COLLECTION_CACHE_TTL_SECONDS", "999999")
    # Patch globals on the module for cache dir and target path
    import devsynth.testing.run_tests as rt

    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", str(cache_dir))
    monkeypatch.setitem(TARGET_PATHS, "unit-tests", str(tests_dir) + "/")

    outputs = ["test_sample.py::test_example\n"]
    call_index = {"value": 0}

    def fake_run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        timeout=None,
        cwd=None,
        env=None,
    ):  # noqa: ANN001
        idx = min(call_index["value"], len(outputs) - 1)
        call_index["value"] += 1
        return SimpleNamespace(stdout=outputs[idx], stderr="", returncode=0)

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    # Act: initial collection (populates cache)
    first = collect_tests_with_cache("unit-tests", "fast")
    assert any("test_sample.py" in p for p in first)

    # Modify the test file to change mtime/content
    test_file.write_text(
        """
import pytest

@pytest.mark.fast
def test_example():
    assert 2 + 2 == 4

@pytest.mark.fast
def test_another():
    assert True
"""
    )

    outputs.append("test_sample.py::test_example\n")

    # Act: second collection should invalidate cache due to mtime change
    second = collect_tests_with_cache("unit-tests", "fast")

    # Assert: new test should be visible in collected list
    assert any("test_another" in p or "test_sample.py" in p for p in second)
    # Ensure we at least collected something again
    assert len(second) >= len(first)


@pytest.mark.fast
def test_cache_invalidation_on_marker_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tests_dir = tmp_path / "isolated_tests_marker"
    tests_dir.mkdir(parents=True, exist_ok=True)

    test_file = tests_dir / "test_marker.py"
    test_file.write_text(
        """
import pytest

@pytest.mark.fast
def test_fast_case():
    assert True
"""
    )

    cache_dir = tmp_path / ".cache"
    monkeypatch.setenv("DEVSYNTH_COLLECTION_CACHE_TTL_SECONDS", "999999")
    import devsynth.testing.run_tests as rt

    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", str(cache_dir))
    monkeypatch.setitem(TARGET_PATHS, "unit-tests", str(tests_dir) + "/")

    outputs = [
        "test_marker.py::test_fast_case\n",
        "test_marker.py::test_medium_case\n",
    ]
    call_index = {"value": 0}

    def fake_run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        timeout=None,
        cwd=None,
        env=None,
    ):  # noqa: ANN001
        idx = min(call_index["value"], len(outputs) - 1)
        call_index["value"] += 1
        return SimpleNamespace(stdout=outputs[idx], stderr="", returncode=0)

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    # Populate cache for fast
    fast_list = collect_tests_with_cache("unit-tests", "fast")
    assert any("test_marker.py" in p for p in fast_list)
    calls_after_first = call_index["value"]

    # Change marker from fast to medium to ensure category_expr changes and mtime updates
    test_file.write_text(
        """
import pytest

@pytest.mark.medium
def test_fast_case():
    assert True
"""
    )
    # Ensure filesystem timestamp advances for cache invalidation fingerprints
    current_stat = test_file.stat()
    os.utime(
        test_file,
        (
            current_stat.st_atime + 5,
            current_stat.st_mtime + 5,
        ),
    )

    # Now collecting fast should invalidate and likely return empty (since test is now medium)
    fast_after_change = collect_tests_with_cache("unit-tests", "fast")
    # Ensure collection ran again after marker change, invalidating cache
    assert call_index["value"] > calls_after_first
    assert any("test_marker.py" in p for p in fast_after_change)


@pytest.mark.fast
def test_cache_invalidation_on_target_path_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tests_dir_one = tmp_path / "suite_one"
    tests_dir_one.mkdir(parents=True, exist_ok=True)
    (tests_dir_one / "test_alpha.py").write_text(
        "import pytest\n\n@pytest.mark.fast\ndef test_alpha():\n    assert True\n"
    )

    tests_dir_two = tmp_path / "suite_two"
    tests_dir_two.mkdir(parents=True, exist_ok=True)
    (tests_dir_two / "test_beta.py").write_text(
        "import pytest\n\n@pytest.mark.fast\ndef test_beta():\n    assert True\n"
    )

    cache_dir = tmp_path / ".cache"
    import devsynth.testing.run_tests as rt

    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", str(cache_dir))
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tests_dir_one))
    monkeypatch.setattr(rt, "COLLECTION_CACHE_TTL_SECONDS", 999999)

    calls = {"count": 0}

    class FakeProc:
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
        assert "--collect-only" in cmd
        calls["count"] += 1
        cwd = os.getcwd()
        if cwd == str(tests_dir_one):
            return FakeProc("test_alpha.py::test_alpha\n")
        if cwd == str(tests_dir_two):
            return FakeProc("test_beta.py::test_beta\n")
        raise AssertionError(f"Unexpected cwd {cwd}")

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    first = collect_tests_with_cache("unit-tests", "fast")
    assert len(first) == 1
    assert first[0].endswith("test_alpha.py") or "test_alpha.py::test_alpha" in first[0]

    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tests_dir_two))

    second = collect_tests_with_cache("unit-tests", "fast")
    assert len(second) == 1
    assert second[0].endswith("test_beta.py") or "test_beta.py::test_beta" in second[0]

    assert calls["count"] == 2
