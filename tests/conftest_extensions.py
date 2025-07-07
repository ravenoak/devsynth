"""
Extensions to pytest configuration for test categorization and organization.
"""

import pytest
import time
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path

# Global dictionary to store test times
# This is used by the TestCategorization plugin
test_times: Dict[str, float] = {}

# Define markers for test speed
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "fast: mark test as fast (execution time < 1s)")
    config.addinivalue_line("markers", "medium: mark test as medium speed (execution time between 1s and 5s)")
    config.addinivalue_line("markers", "slow: mark test as slow (execution time > 5s)")

    # Register the plugin
    config.pluginmanager.register(TestCategorization(), "test_categorization")

class TestCategorization:
    """Plugin for test categorization and organization."""

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

            # Automatically mark tests based on execution time
            if item._duration < 1.0:
                item.add_marker(pytest.mark.fast)
            elif item._duration < 5.0:
                item.add_marker(pytest.mark.medium)
            else:
                item.add_marker(pytest.mark.slow)

    @pytest.hookimpl(trylast=True)
    def pytest_terminal_summary(self, terminalreporter):
        """Add test categorization summary to terminal report."""
        tr = terminalreporter

        # Skip if no tests were collected
        if not tr.stats:
            return

        tr.write_sep("=", "Test Categorization Summary")

        # Count tests by category
        categories = {
            "unit": 0,
            "integration": 0,
            "behavior": 0,
            "fast": 0,
            "medium": 0,
            "slow": 0
        }

        for item in tr.stats.get("passed", []) + tr.stats.get("failed", []) + tr.stats.get("skipped", []):
            # Categorize by test type
            if "unit" in item.nodeid:
                categories["unit"] += 1
            elif "integration" in item.nodeid:
                categories["integration"] += 1
            elif "behavior" in item.nodeid:
                categories["behavior"] += 1

            # Categorize by speed
            nodeid = item.nodeid
            duration = test_times.get(nodeid, 0)
            if duration < 1.0:
                categories["fast"] += 1
            elif duration < 5.0:
                categories["medium"] += 1
            else:
                categories["slow"] += 1

        # Print summary
        tr.write_line("Test Type Distribution:")
        tr.write_line(f"  Unit Tests: {categories['unit']}")
        tr.write_line(f"  Integration Tests: {categories['integration']}")
        tr.write_line(f"  Behavior Tests: {categories['behavior']}")
        tr.write_line("")
        tr.write_line("Test Speed Distribution:")
        tr.write_line(f"  Fast Tests (< 1s): {categories['fast']}")
        tr.write_line(f"  Medium Tests (1-5s): {categories['medium']}")
        tr.write_line(f"  Slow Tests (> 5s): {categories['slow']}")

        # Print slowest tests
        if test_times:
            tr.write_sep("=", "Top 10 Slowest Tests")
            sorted_times = sorted(test_times.items(), key=lambda x: x[1], reverse=True)
            for i, (nodeid, duration) in enumerate(sorted_times[:10]):
                tr.write_line(f"{i+1}. {nodeid}: {duration:.2f}s")

def pytest_addoption(parser):
    """Add command-line options for test categorization."""
    group = parser.getgroup("test_categorization")
    group.addoption(
        "--speed",
        action="store",
        choices=["fast", "medium", "slow", "all"],
        default="all",
        help="Run tests based on execution speed (fast, medium, slow, or all)"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection based on categorization options."""
    # Filter by speed if specified
    speed = config.getoption("--speed")
    if speed != "all":
        skip_other_speeds = pytest.mark.skip(reason=f"Test speed doesn't match --speed={speed}")
        for item in items:
            # Get the test duration if available
            nodeid = item.nodeid
            duration = getattr(item, "_duration", None)

            # If we don't have duration yet (first run), estimate based on markers
            if duration is None:
                if speed == "fast" and not item.get_closest_marker("fast"):
                    item.add_marker(skip_other_speeds)
                elif speed == "medium" and not item.get_closest_marker("medium"):
                    item.add_marker(skip_other_speeds)
                elif speed == "slow" and not item.get_closest_marker("slow"):
                    item.add_marker(skip_other_speeds)
            else:
                # We have actual duration data
                if speed == "fast" and duration >= 1.0:
                    item.add_marker(skip_other_speeds)
                elif speed == "medium" and (duration < 1.0 or duration >= 5.0):
                    item.add_marker(skip_other_speeds)
                elif speed == "slow" and duration < 5.0:
                    item.add_marker(skip_other_speeds)
