# Central integration test speed marker enforcement
#
# Purpose:
# - Ensure exactly one speed marker at the function level for tests
#   under tests/integration/**.
# - Default integration tests to medium speed unless explicitly marked.
# - Avoid adding a second speed marker if a function-level speed marker is
#   already present.
#
# Rationale:
# - Aligns with docs/plan.md Verification Protocol and docs/tasks.md
#   P1.1 subtask 1.3.
# - Mirrors the behavior-suite centralization pattern to reduce scattered,
#   fragile per-file hooks.
#
# Notes:
# - We intentionally inspect item.own_markers (function/class level)
#   instead of get_closest_marker because the latter may include
#   module-level markers, which our verifier does not accept for speed
#   categories.

from __future__ import annotations

import pytest

from tests.fixtures import optional_deps

_SPEED_MARKER_NAMES = {"fast", "medium", "slow"}


def _is_in_integration_dir(item: pytest.Item) -> bool:
    # item.fspath is a py.path object (stringifiable). Works across pytest
    # versions.
    try:
        fspath = str(item.fspath)
    except Exception:
        # Fallback to nodeid for safety
        fspath = getattr(item, "nodeid", "")
    return "/tests/integration/" in fspath or fspath.startswith("tests/integration/")


def _has_function_level_speed_marker(item: pytest.Item) -> bool:
    # Use own_markers to focus on function/class level only
    # (exclude module-level markers).
    own = getattr(item, "own_markers", []) or []
    for m in own:
        try:
            if m.name in _SPEED_MARKER_NAMES:
                return True
        except Exception:
            # Be tolerant to unusual marker objects
            continue
    return False


def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
) -> None:
    for item in items:
        if not _is_in_integration_dir(item):
            continue
        if _has_function_level_speed_marker(item):
            continue
        # Apply default medium speed for integration tests missing a
        # function-level speed marker.
        item.add_marker(pytest.mark.medium)


@pytest.fixture(autouse=True)
def _stub_external_services():
    """Automatically stub optional external dependencies for integration tests."""
    # Apply optional dependency stubs
    optional_deps._apply_optional_stubs()
    return None
