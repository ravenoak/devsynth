import pytest

from devsynth.domain.models.wsde_enhanced_dialectical import (
    _categorize_critiques_by_domain,
    _identify_domain_conflicts,
)


@pytest.mark.fast
def test_categorize_critiques_by_domain_groups_terms():
    """ReqID: WSDE-ENHANCED-01 — groups critiques by domain keywords."""
    critiques = [
        "Possible SQL injection",
        "Slow performance",
        "Needs example",
    ]
    categories = _categorize_critiques_by_domain(critiques)
    assert "Possible SQL injection" in categories["security"]
    assert "Slow performance" in categories["performance"]
    assert "Needs example" in categories["examples"]


@pytest.mark.fast
def test_identify_domain_conflicts_finds_performance_security():
    """ReqID: WSDE-ENHANCED-02 — detects performance vs security conflicts."""
    domain_critiques = {"performance": ["slow"], "security": ["injection"]}
    conflicts = _identify_domain_conflicts(domain_critiques)
    assert {"domain1": "performance", "domain2": "security"} in conflicts
