"""
Extensions to pytest configuration for test categorization and organization.
"""

import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest

test_times: Dict[str, float] = {}


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "fast: mark test as fast (execution time < 1s)")
    config.addinivalue_line(
        "markers",
        "medium: mark test as medium speed (execution time between 1s and 5s)",
    )
    config.addinivalue_line("markers", "slow: mark test as slow (execution time > 5s)")
    config.pluginmanager.register(TestCategorization(), "test_categorization")


class TestCategorization:
    """Plugin for test categorization and organization.

    ReqID: N/A"""

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_setup(self, item):
        """Set up timing for test execution."""
        item._start_time = time.time()

    @pytest.hookimpl(trylast=True)
    def pytest_runtest_teardown(self, item):
        """Record test execution time."""
        if hasattr(item, "_start_time"):
            item._duration = time.time() - item._start_time
            test_times[item.nodeid] = item._duration

    @pytest.hookimpl(trylast=True)
    def pytest_terminal_summary(self, terminalreporter):
        """Add test categorization summary to terminal report."""
        tr = terminalreporter
        if not tr.stats:
            return
        tr.write_sep("=", "Test Categorization Summary")
        categories = {
            "unit": 0,
            "integration": 0,
            "behavior": 0,
            "fast": 0,
            "medium": 0,
            "slow": 0,
        }
        for item in (
            tr.stats.get("passed", [])
            + tr.stats.get("failed", [])
            + tr.stats.get("skipped", [])
        ):
            if "unit" in item.nodeid:
                categories["unit"] += 1
            elif "integration" in item.nodeid:
                categories["integration"] += 1
            elif "behavior" in item.nodeid:
                categories["behavior"] += 1
            nodeid = item.nodeid
            duration = test_times.get(nodeid, 0)
            if duration < 1.0:
                categories["fast"] += 1
            elif duration < 5.0:
                categories["medium"] += 1
            else:
                categories["slow"] += 1
        tr.write_line("Test Type Distribution:")
        tr.write_line(f"  Unit Tests: {categories['unit']}")
        tr.write_line(f"  Integration Tests: {categories['integration']}")
        tr.write_line(f"  Behavior Tests: {categories['behavior']}")
        tr.write_line("")
        tr.write_line("Test Speed Distribution:")
        tr.write_line(f"  Fast Tests (< 1s): {categories['fast']}")
        tr.write_line(f"  Medium Tests (1-5s): {categories['medium']}")
        tr.write_line(f"  Slow Tests (> 5s): {categories['slow']}")
        if test_times:
            tr.write_sep("=", "Top 10 Slowest Tests")
            sorted_times = sorted(test_times.items(), key=lambda x: x[1], reverse=True)
            for i, (nodeid, duration) in enumerate(sorted_times[:10]):
                tr.write_line(f"{i + 1}. {nodeid}: {duration:.2f}s")


def pytest_addoption(parser):
    """Add command-line options for test categorization."""
    group = parser.getgroup("test_categorization")
    group.addoption(
        "--speed",
        action="store",
        choices=["fast", "medium", "slow", "all"],
        default="all",
        help="Run tests based on execution speed (fast, medium, slow, or all)",
    )


def pytest_collection_modifyitems(config, items):
    """Validate test speed markers and apply filtering.

    Harmonization rules:
    - Do not auto-add a default speed marker here; centralized suite conftests
      (tests/unit|integration|behavior/conftest.py) are authoritative for defaults.
    - Only warn when a test lacks exactly one speed marker; let the verifier and
      suite hooks drive remediation. Apply --speed filtering only when a single
      speed marker is present.
    """
    speed = config.getoption("--speed")
    skip_other_speeds = None
    if speed != "all":
        skip_other_speeds = pytest.mark.skip(
            reason=f"Test speed doesn't match --speed={speed}"
        )
    for item in items:
        speed_markers = [
            name for name in ("fast", "medium", "slow") if item.get_closest_marker(name)
        ]
        marker = None
        if len(speed_markers) != 1:
            # Emit a warning so contributors add an explicit marker in-source.
            try:
                item.warn(
                    pytest.PytestWarning(
                        f"Test '{item.nodeid}' lacks exactly one speed marker; please add @pytest.mark.fast|medium|slow at function level"
                    )
                )
            except Exception:
                pass
        else:
            marker = speed_markers[0]
        # Only apply --speed filtering when we have an unambiguous marker
        if marker and skip_other_speeds and marker != speed:
            item.add_marker(skip_other_speeds)

    # Apply flaky retries to online resource-marked tests if configured
    try:
        import os

        retries_raw = os.environ.get("DEVSYNTH_ONLINE_TEST_RETRIES", "2").strip()
        delay_raw = os.environ.get("DEVSYNTH_ONLINE_TEST_RETRY_DELAY", "0").strip()
        retries = int(retries_raw) if retries_raw != "" else 2
        delay = int(delay_raw) if delay_raw != "" else 0
    except Exception:
        retries, delay = 2, 0

    if retries > 0:
        for item in items:
            if item.get_closest_marker("requires_resource"):
                # Add a flaky marker understood by pytest-rerunfailures if installed.
                try:
                    item.add_marker(
                        pytest.mark.flaky(reruns=retries, reruns_delay=delay)
                    )
                except Exception:
                    # If plugin is unavailable, marker is inert; behavior remains unchanged.
                    pass
