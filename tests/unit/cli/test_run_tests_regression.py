import re

import pytest

from devsynth.testing.run_tests import run_tests


@pytest.mark.fast
def test_cli_run_tests_unit_fast_completes_with_non_zero_tests(monkeypatch):
    """
    Regression test: ensure the shared test runner completes in fast mode and
    executes a non-zero number of tests, without hanging on optional providers.
    """
    # Disable optional external providers to avoid network/UI stalls
    monkeypatch.setenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "false")

    success, output = run_tests(
        target="unit-tests",
        speed_categories=("fast",),
        verbose=False,
        report=False,
        parallel=False,  # run in-process to minimize flakiness on CI
        segment=False,
        segment_size=50,
        maxfail=1,
    )

    # Must succeed overall
    assert success, f"Runner did not succeed. Output:\n{output}"

    # Must have a non-zero collection
    # Heuristics: pytest prints 'collected N items'; ensure N > 0
    m = re.search(r"collected\s+(\d+)\s+items?", output)
    assert m is not None, f"Could not find collection count in output:\n{output}"
    assert (
        int(m.group(1)) > 0
    ), f"Expected non-zero tests collected, got 0. Output:\n{output}"
