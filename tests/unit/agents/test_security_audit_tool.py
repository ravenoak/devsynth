"""Tests for the security_audit_tool."""

from types import ModuleType
from unittest.mock import patch

import pytest

from devsynth.agents.tools import get_tool_registry, security_audit_tool

pytestmark = [pytest.mark.fast]


def test_security_audit_tool_returns_structure() -> None:
    """security_audit_tool should return success and captured output."""

    module = ModuleType("security_audit_cmd")

    def _stub(
        skip_static=False,
        skip_safety=False,
        skip_secrets=False,
        skip_owasp=False,
        *,
        bridge,
    ) -> None:
        bridge.display_result("ok")

    module.security_audit_cmd = _stub
    with patch.dict(
        "sys.modules",
        {
            "devsynth.application": ModuleType("application"),
            "devsynth.application.cli": ModuleType("cli"),
            "devsynth.application.cli.commands": ModuleType("commands"),
            "devsynth.application.cli.commands.security_audit_cmd": module,
        },
    ):
        result = security_audit_tool()
    assert result == {"success": True, "output": "ok"}


def test_security_audit_tool_registered() -> None:
    """The tool should be present in the global registry."""

    registry = get_tool_registry()
    func = registry.get("security_audit")
    assert func is not None

    module = ModuleType("security_audit_cmd")

    called = {}

    def _stub(
        skip_static=False,
        skip_safety=False,
        skip_secrets=False,
        skip_owasp=False,
        *,
        bridge,
    ) -> None:
        called["flag"] = True

    module.security_audit_cmd = _stub
    with patch.dict(
        "sys.modules",
        {
            "devsynth.application": ModuleType("application"),
            "devsynth.application.cli": ModuleType("cli"),
            "devsynth.application.cli.commands": ModuleType("commands"),
            "devsynth.application.cli.commands.security_audit_cmd": module,
        },
    ):
        func()
    assert called.get("flag")
