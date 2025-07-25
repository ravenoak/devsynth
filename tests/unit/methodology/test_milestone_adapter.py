from devsynth.methodology.milestone import MilestoneAdapter
from devsynth.methodology.base import Phase


def test_should_start_cycle():
    adapter = MilestoneAdapter({"settings": {"approvalRequired": {}}})
    assert adapter.should_start_cycle()


def test_progress_requires_approval_when_configured():
    settings = {"approvalRequired": {"afterExpand": True}}
    adapter = MilestoneAdapter({"settings": settings})
    results = {"phase_complete": True}
    assert not adapter.should_progress_to_next_phase(Phase.EXPAND, {}, results)
    results["approved"] = True
    assert adapter.should_progress_to_next_phase(Phase.EXPAND, {}, results)
