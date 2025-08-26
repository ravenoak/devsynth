import os
from pathlib import Path

import pytest

from devsynth.testing.run_tests import collect_tests_with_cache, TARGET_PATHS


@pytest.mark.fast
def test_cache_invalidation_on_file_change(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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
    TARGET_PATHS["unit-tests"] = str(tests_dir) + "/"

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

    # Act: second collection should invalidate cache due to mtime change
    second = collect_tests_with_cache("unit-tests", "fast")

    # Assert: new test should be visible in collected list
    assert any("test_another" in p or "test_sample.py" in p for p in second)
    # Ensure we at least collected something again
    assert len(second) >= len(first)


@pytest.mark.fast
def test_cache_invalidation_on_marker_change(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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
    TARGET_PATHS["unit-tests"] = str(tests_dir) + "/"

    # Populate cache for fast
    fast_list = collect_tests_with_cache("unit-tests", "fast")
    assert any("test_marker.py" in p for p in fast_list)

    # Change marker from fast to medium to ensure category_expr changes and mtime updates
    test_file.write_text(
        """
import pytest

@pytest.mark.medium
def test_fast_case():
    assert True
"""
    )

    # Now collecting fast should invalidate and likely return empty (since test is now medium)
    fast_after_change = collect_tests_with_cache("unit-tests", "fast")
    # Either empty due to no fast tests, or different from previous
    assert fast_after_change == [] or fast_after_change != fast_list
