import pytest

"""Unit tests for wsde_code_improvements submodule."""
from devsynth.domain.models.wsde_facade import WSDETeam


class TestWSDECodeImprovements:
    """Tests for code improvement helper methods."""

    def setup_method(self):
        self.team = WSDETeam(name="improve_test")

    def test_improve_credentials_inserts_validation(self):
        code = "def auth(username, password):\n    return username == 'admin' and password == 'password'"
        improved = self.team._improve_credentials(code)
        assert "validate_credentials" in improved
        assert "username == 'admin'" not in improved
