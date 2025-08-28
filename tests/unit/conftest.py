# Central unit test speed marker enforcement
#
# Purpose:
# - Ensure exactly one speed marker at the function level for tests under tests/unit/**.
# - Default unit tests to fast unless explicitly marked otherwise.
# - Avoid adding a second speed marker if a function-level speed marker is already present.
#
# Rationale:
# - Aligns with docs/plan.md Verification Protocol and docs/tasks.md P1.1 subtask 1.2.
# - Mirrors the behavior/integration centralization pattern to reduce scattered, repetitive edits.
# - Keeps diffs minimal and adheres to .junie/guidelines.md (clarity, determinism, hermeticity).

from __future__ import annotations

import pytest

_SPEED_MARKER_NAMES = {"fast", "medium", "slow"}


def _is_in_unit_dir(item: pytest.Item) -> bool:
    # item.fspath is a py.path object (stringifiable). Works across pytest versions.
    try:
        fspath = str(item.fspath)
    except Exception:
        # Fallback to nodeid for safety
        fspath = getattr(item, "nodeid", "")
    return "/tests/unit/" in fspath or fspath.startswith("tests/unit/")


def _has_function_level_speed_marker(item: pytest.Item) -> bool:
    # Use own_markers to focus on function/class level only (exclude module-level markers).
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
        if not _is_in_unit_dir(item):
            continue
        if _has_function_level_speed_marker(item):
            continue
        # Apply default fast speed for unit tests missing a function-level speed marker.
        item.add_marker(pytest.mark.fast)
