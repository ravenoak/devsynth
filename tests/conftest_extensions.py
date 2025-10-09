"""Extensions to pytest configuration for test categorization and organization."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Iterable, List

import pytest

from tests.fixtures import resources as resource_helpers

try:  # Python 3.11 fallback when running in older virtualenvs locally
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - compatibility shim for 3.11
    import tomli as tomllib

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_DECLARED_MARKERS: set[str] = set()
_AD_HOC_WARNED: set[str] = set()

_SAFE_RUNTIME_MARKERS = {
    "parametrize",
    "skip",
    "skipif",
    "xfail",
    "usefixtures",
    "filterwarnings",
}
_DERIVED_MARKER_PREFIXES = {"resource_"}
_AD_HOC_MARKERS = {"asyncio", "anyio"}

test_times: dict[str, float] = {}


def _iter_resource_markers(item: pytest.Item) -> Iterable[str]:
    """Yield resource names declared via ``@pytest.mark.requires_resource``."""

    for mark in item.iter_markers(name="requires_resource"):
        resource: str | None = None
        if mark.args:
            candidate = mark.args[0]
            if isinstance(candidate, str):
                resource = candidate
        elif "resource" in mark.kwargs:
            candidate = mark.kwargs.get("resource")
            if isinstance(candidate, str):
                resource = candidate
        if resource:
            yield resource


def _ensure_resource_skip_markers(item: pytest.Item) -> None:
    """Attach skip markers for unavailable optional backends."""

    seen: set[str] = set()
    for resource in _iter_resource_markers(item):
        if resource in seen:
            continue
        seen.add(resource)
        markers = resource_helpers.skip_if_missing_backend(
            resource,
            include_requires_resource=False,
        )
        for mark in markers:
            item.add_marker(mark)


def _load_declared_markers() -> dict[str, str]:
    """Return normalized marker definitions from pyproject.toml."""

    pyproject = PROJECT_ROOT / "pyproject.toml"
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except Exception:
        return {}
    markers_section = (
        data.get("tool", {}).get("pytest", {}).get("ini_options", {}).get("markers", [])
    )
    declared: dict[str, str] = {}
    for entry in markers_section or []:
        if not isinstance(entry, str):
            continue
        name_part, _, description = entry.partition(":")
        base = name_part.split("(", 1)[0].strip()
        if not base:
            continue
        declared[base] = description.strip()
    return declared


def _ensure_marker_registered(
    config: pytest.Config, name: str, description: str
) -> None:
    """Register a marker with pytest if not already present."""

    summary = description or "auto-registered from pyproject.toml"
    config.addinivalue_line("markers", f"{name}: {summary}")


def _warn_on_ad_hoc_marker(item: pytest.Item, marker: str) -> None:
    """Emit a single warning for markers missing from the canonical registry."""

    if marker in _AD_HOC_WARNED:
        return
    message = (
        "Marker '{marker}' is not declared in pyproject.toml. "
        "Request registration via docs/testing/verify_test_markers.md."
    )
    try:
        item.warn(pytest.PytestWarning(message.format(marker=marker)))
    except Exception:
        pass
    _AD_HOC_WARNED.add(marker)


def _warn_on_legacy_marker(item: pytest.Item, marker: str) -> None:
    """Inform contributors about plugin-provided markers we intentionally track."""

    if marker in _AD_HOC_WARNED:
        return
    message = (
        "Marker '{marker}' relies on plugin defaults and is not tracked in "
        "pyproject.toml. Document justification or request registration via "
        "docs/testing/verify_test_markers.md."
    )
    try:
        item.warn(pytest.PytestWarning(message.format(marker=marker)))
    except Exception:
        pass
    _AD_HOC_WARNED.add(marker)


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with custom markers."""

    declared = _load_declared_markers()
    _DECLARED_MARKERS.clear()
    _DECLARED_MARKERS.update(declared)
    for marker, description in declared.items():
        _ensure_marker_registered(config, marker, description)

    # Ensure foundational markers are always registered even if parsing fails.
    for fallback_marker, desc in [
        ("fast", "mark test as fast (execution time < 1s)"),
        ("medium", "mark test as medium speed (execution time between 1s and 5s)"),
        ("slow", "mark test as slow (execution time > 5s)"),
        ("cli", "mark test as part of the CLI verification suite"),
    ]:
        if fallback_marker not in declared:
            _ensure_marker_registered(config, fallback_marker, desc)

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


def pytest_collection_modifyitems(
    config: pytest.Config, items: List[pytest.Item]
) -> None:
    """Validate test speed markers and apply filtering."""

    speed = config.getoption("--speed")
    skip_other_speeds = None
    if speed != "all":
        skip_other_speeds = pytest.mark.skip(
            reason=f"Test speed doesn't match --speed={speed}"
        )
    for item in items:
        _ensure_resource_skip_markers(item)
        speed_markers = [
            name for name in ("fast", "medium", "slow") if item.get_closest_marker(name)
        ]
        marker = None
        if len(speed_markers) != 1:
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

        for mark in item.iter_markers():
            marker_name = mark.name.split("(", 1)[0]
            if marker_name in _DECLARED_MARKERS:
                continue
            if marker_name in _SAFE_RUNTIME_MARKERS:
                continue
            if any(
                marker_name.startswith(prefix) for prefix in _DERIVED_MARKER_PREFIXES
            ):
                continue
            if marker_name in _AD_HOC_MARKERS:
                _warn_on_legacy_marker(item, marker_name)
            else:
                _warn_on_ad_hoc_marker(item, marker_name)

        if marker and skip_other_speeds and marker != speed:
            item.add_marker(skip_other_speeds)

    try:
        import os

        retries_raw = os.environ.get("DEVSYNTH_ONLINE_TEST_RETRIES", "0").strip()
        delay_raw = os.environ.get("DEVSYNTH_ONLINE_TEST_RETRY_DELAY", "0").strip()
        retries = int(retries_raw) if retries_raw != "" else 0
        delay = int(delay_raw) if delay_raw != "" else 0
    except Exception:
        retries, delay = 0, 0

    if retries > 0:
        for item in items:
            if item.get_closest_marker("requires_resource"):
                try:
                    item.add_marker(
                        pytest.mark.flaky(reruns=retries, reruns_delay=delay)
                    )
                except Exception:
                    pass
