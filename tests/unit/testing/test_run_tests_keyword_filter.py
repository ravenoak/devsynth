from pathlib import Path

import pytest

from devsynth.testing.run_tests import run_tests


@pytest.mark.fast
def test_keyword_filter_no_matches_returns_success_message(tmp_path, monkeypatch):
    """ReqID: FR-11.2 — Keyword filter path returns success when no matches.

    Triggers the lmstudio keyword path and expects a friendly message.
    """
    # Ensure no tests contain 'lmstudio' keyword in node ids by running -k filter.
    # We also set CWD to repo root implicitly; run_tests manages collection.
    # Use a very specific marker expression to trigger keyword path.
    success, output = run_tests(
        target="unit-tests",
        speed_categories=None,
        verbose=False,
        report=False,
        parallel=False,
        segment=False,
        extra_marker="requires_resource('lmstudio')",
    )
    assert success is True
    assert "No tests matched" in output


@pytest.mark.fast
def test_keyword_filter_honors_report_flag_and_creates_report_dir(
    monkeypatch, tmp_path
):
    """ReqID: FR-11.2 — Report flag creates deterministic report directory.

    Use keyword path with report=True and patch datetime to assert directory path.
    """
    from devsynth.testing import run_tests as rt

    class FakeDT:
        @staticmethod
        def now():
            # Fixed timestamp for stable directory path
            class _DT:
                def strftime(self, fmt: str) -> str:
                    return "20250101_000000"

            return _DT()

    monkeypatch.setattr(rt, "datetime", FakeDT)

    success, output = run_tests(
        target="unit-tests",
        speed_categories=None,
        verbose=False,
        report=True,
        parallel=False,
        segment=False,
        extra_marker='requires_resource("lmstudio")',
    )
    assert success is True
    # Report path is logged; ensure directory exists
    expected_dir = Path("test_reports/20250101_000000/unit-tests")
    assert expected_dir.exists()
