"""Unit tests for wsde_code_improvements helpers exposed via WSDETeam."""

from __future__ import annotations

import pytest


@pytest.mark.fast
def test_improve_credentials_inserts_validation(wsde_module_team):
    """ReqID: WSDE-CODE-01 — replaces hardcoded credentials and injects validator."""

    team, _ = wsde_module_team
    code = "def auth(username, password):\n    return username == 'admin' and password == 'password'"

    improved = team._improve_credentials(code)

    assert "def validate_credentials" in improved
    assert "username == 'admin'" not in improved


@pytest.mark.fast
def test_improve_credentials_noop_when_already_secure(wsde_module_team):
    """ReqID: WSDE-CODE-02 — leaves sanitized authentication routine unchanged."""

    team, _ = wsde_module_team
    code = """
def validate_credentials(username, password):
    return username and password


def auth(username, password):
    return validate_credentials(username, password)
""".strip()

    improved = team._improve_credentials(code)

    assert improved == code


@pytest.mark.fast
def test_improve_error_handling_wraps_body(wsde_module_team):
    """ReqID: WSDE-CODE-03 — guards processing routines with try/except blocks."""

    team, _ = wsde_module_team
    code = """
def process(data):
    return data[0]
""".strip()

    improved = team._improve_error_handling(code)

    assert "try:" in improved
    assert "except Exception as e" in improved
