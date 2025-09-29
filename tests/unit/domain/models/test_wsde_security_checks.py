"""Unit tests for wsde_security_checks submodule."""

import pytest


@pytest.mark.fast
def test_check_security_best_practices_detects_issue(wsde_team_factory):
    """ReqID: WSDE-SECURITY-01 — flags insecure patterns for escalation."""

    team = wsde_team_factory()
    insecure_code = "password = 'secret'\nexec('print(1)')\n"
    assert team._check_security_best_practices(insecure_code) is False


@pytest.mark.fast
def test_check_security_best_practices_accepts_clean_code(wsde_team_factory):
    """ReqID: WSDE-SECURITY-02 — passes checklist when code avoids red flags."""

    team = wsde_team_factory()
    secure_code = (
        "def process_items(items):\n"
        "    processed_items = []\n"
        "    for element in items:\n"
        "        processed_items.append(element)\n"
        "    return processed_items\n"
    )
    assert team._check_security_best_practices(secure_code) is True


@pytest.mark.fast
def test_balance_security_and_performance_idempotent(wsde_team_factory):
    """ReqID: WSDE-SECURITY-03 — avoids duplicating checklist annotations."""

    team = wsde_team_factory()
    code = "def run():\n    return True"

    balanced_once = team._balance_security_and_performance(code)
    balanced_twice = team._balance_security_and_performance(balanced_once)

    assert balanced_once == balanced_twice
    assert balanced_once.count("Security and performance balance") == 1
