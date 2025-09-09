from pathlib import Path

import pytest

from devsynth.testing.run_tests import TARGET_PATHS, run_tests


@pytest.mark.fast
def test_html_report_artifacts_created_with_stable_naming(tmp_path, monkeypatch):
    """
    Verify that --report produces an HTML report under test_reports/ with a
    timestamped folder and target subdirectory, and that the naming is stable
    enough for tooling (YYYYMMDD_HHMMSS/target/report.html).
    """
    # Arrange: create a minimal passing test in an isolated directory
    test_file = tmp_path / "test_passes.py"
    test_file.write_text(
        """
import pytest

@pytest.mark.fast
def test_will_pass():
    assert True
"""
    )
    # Route the unit-tests target to our isolated directory
    monkeypatch.setitem(TARGET_PATHS, "unit-tests", str(tmp_path))

    # Act: run tests with HTML report generation enabled
    success, output = run_tests("unit-tests", ["fast"], report=True, parallel=False)

    # Assert: tests should pass and a report should be created in test_reports/
    assert success, f"Expected success, got failure. Output was:\n{output}"

    reports_root = Path("test_reports")
    assert reports_root.exists(), "test_reports directory should be created"

    # Find any report.html generated for unit-tests; choose the newest one
    candidates = list(reports_root.glob("*/unit-tests/report.html"))
    assert (
        candidates
    ), "Expected at least one report.html under test_reports/*/unit-tests/"

    latest = max(candidates, key=lambda p: p.stat().st_mtime)
    # Basic stability checks on folder naming: YYYYMMDD_HHMMSS
    timestamp_folder = latest.parents[1].name  # the */ part under test_reports/
    assert len(timestamp_folder) == 15, "Timestamp folder should be YYYYMMDD_HHMMSS"
    assert timestamp_folder[8] == "_", "Timestamp separator should be an underscore"
    assert timestamp_folder.replace(
        "_", ""
    ).isdigit(), "Timestamp should be numeric digits around underscore"

    # The file should exist and be non-empty
    assert latest.is_file(), "report.html should be a file"
    assert latest.stat().st_size > 0, "report.html should not be empty"
