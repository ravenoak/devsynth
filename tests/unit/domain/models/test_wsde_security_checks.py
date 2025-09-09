"""Unit tests for wsde_security_checks submodule."""

import pytest

from devsynth.domain.models.wsde_facade import WSDETeam


class TestWSDESecurityChecks:
    """Tests for security check helper methods."""

    def setup_method(self):
        self.team = WSDETeam(name="sec_test")

    @pytest.mark.fast
    def test_check_security_best_practices_detects_issue(self):
        insecure_code = "password = 'secret'\n"
        assert self.team._check_security_best_practices(insecure_code) is False

    @pytest.mark.fast
    def test_balance_security_and_performance_adds_comment(self):
        code = "def run():\n    pass"
        balanced = self.team._balance_security_and_performance(code)
        assert "Security and performance balance" in balanced
