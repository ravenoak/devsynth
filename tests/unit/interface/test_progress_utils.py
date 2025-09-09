from typing import Any

import pytest

from devsynth.interface.progress_utils import (
    ProgressManager,
    ProgressTracker,
    StepProgress,
    create_progress_manager,
    progress_indicator,
    track_progress,
)


class FakeIndicator:
    def __init__(self) -> None:
        self.updates: list[dict[str, Any]] = []
        self.completed: bool = False

    def update(
        self,
        *,
        advance: int = 0,
        description: str | None = None,
        status: str | None = None,
    ) -> None:
        self.updates.append(
            {"advance": advance, "description": description, "status": status}
        )

    def complete(self) -> None:
        self.completed = True


class FakeBridge:
    def __init__(self) -> None:
        self.created: list[dict[str, Any]] = []
        self.last_indicator: FakeIndicator | None = None

    def create_progress(
        self, description: str, total: int = 100
    ) -> FakeIndicator:  # noqa: D401 - simple fake
        self.created.append({"description": description, "total": total})
        self.last_indicator = FakeIndicator()
        return self.last_indicator


@pytest.mark.fast
def test_progress_manager_create_get_complete_and_context_manager():
    """ReqID: IF-PR-01 — PM create/get/complete and context manager semantics."""
    bridge = FakeBridge()
    mgr = ProgressManager(bridge)

    # Create with key and retrieve it
    ind = mgr.create("work", total=3, key="k1")
    assert mgr.get("k1") is ind

    # Context manager auto-completes and removes
    with mgr.progress("ctx", total=2, key="k2") as ind2:
        assert mgr.get("k2") is ind2
        assert not ind2.completed
    assert mgr.get("k2") is None

    # Explicit complete removes and marks complete
    mgr.complete("k1")
    assert ind.completed is True
    assert mgr.get("k1") is None


@pytest.mark.fast
def test_progress_manager_track_updates_on_item_and_slice():
    """ReqID: IF-PR-02 — tracking advances via __getitem__ for item and slice."""
    bridge = FakeBridge()
    mgr = ProgressManager(bridge)

    items = [10, 20, 30, 40]
    tracked = mgr.track(items, "processing", key="batch")
    # Access one item (advance by 1) and a slice of two (advance by 2)
    _ = tracked[0]
    _ = tracked[1:3]

    ind = bridge.last_indicator
    assert ind is not None
    advances = [u["advance"] for u in ind.updates]
    # First access is 1, slice count is 2
    assert 1 in advances and 2 in advances


@pytest.mark.fast
def test_progress_indicator_context_manager_completes():
    """ReqID: IF-PR-03 — progress_indicator completes on context exit."""
    bridge = FakeBridge()
    with progress_indicator(bridge, "doing", total=5) as ind:
        assert isinstance(ind, FakeIndicator)
        assert not ind.completed
    assert ind.completed is True


@pytest.mark.fast
def test_step_progress_sequencing_and_complete():
    """ReqID: IF-PR-04 — StepProgress sequencing across steps and completion."""
    bridge = FakeBridge()
    steps = ["s1", "s2", "s3"]
    sp = StepProgress(bridge, steps)

    # First advance should set description without advancing count (0)
    sp.advance()
    # Subsequent advances increment
    sp.advance()
    # Complete should finish any remaining and mark complete
    sp.complete()

    ind = bridge.last_indicator
    assert ind is not None
    # Ensure at least one update had advance=0 and one had advance=1
    advances = [u["advance"] for u in ind.updates]
    assert 0 in advances and 1 in advances
    assert ind.completed is True


@pytest.mark.fast
def test_create_and_track_progress_helpers_use_manager():
    """ReqID: IF-PR-05 — helper functions create and track progress via manager."""
    bridge = FakeBridge()
    mgr = create_progress_manager(bridge)
    assert isinstance(mgr, ProgressManager)

    data = list(range(3))
    tracked = track_progress(bridge, data, "t")
    # Access all items via indexing to trigger __getitem__ side effects
    for i in range(len(tracked)):
        _ = tracked[i]
    ind = bridge.last_indicator
    assert ind is not None
    # Three items accessed => at least three update calls recorded
    # (may be more from context enter)
    assert sum(1 for u in ind.updates if u["advance"] == 1) >= 3


@pytest.mark.fast
def test_progress_tracker_forced_update_and_complete():
    """ReqID: IF-PR-06 — Tracker forced update bypasses throttle and completes."""
    ind = FakeIndicator()
    tracker = ProgressTracker(
        indicator=ind, total=None, update_interval=999.0, auto_complete=True
    )

    # Force an update to bypass the time throttle path
    tracker.update(advance=5, force=True)
    # Status text should contain a percentage and description updated
    assert any(u["status"] and "% complete" in u["status"] for u in ind.updates)

    tracker.complete()
    assert ind.completed is True
