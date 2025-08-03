"""Tests for the doctor_tool."""

from types import ModuleType
from unittest.mock import patch

from devsynth.agents.tools import doctor_tool, get_tool_registry


def test_doctor_tool_returns_structure() -> None:
    """doctor_tool should return success and captured output."""

    module = ModuleType("doctor_cmd")

    def _stub(config_dir="config", quick=False, *, bridge) -> None:
        bridge.display_result("ok")

    module.doctor_cmd = _stub
    with patch.dict(
        "sys.modules",
        {
            "devsynth.application": ModuleType("application"),
            "devsynth.application.cli": ModuleType("cli"),
            "devsynth.application.cli.commands": ModuleType("commands"),
            "devsynth.application.cli.commands.doctor_cmd": module,
        },
    ):
        result = doctor_tool()
    assert result == {"success": True, "output": "ok"}


def test_doctor_tool_registered() -> None:
    """The tool should be present in the global registry."""

    registry = get_tool_registry()
    func = registry.get("doctor")
    assert func is not None

    module = ModuleType("doctor_cmd")
    called = {}

    def _stub(config_dir="config", quick=False, *, bridge) -> None:
        called["flag"] = True

    module.doctor_cmd = _stub
    with patch.dict(
        "sys.modules",
        {
            "devsynth.application": ModuleType("application"),
            "devsynth.application.cli": ModuleType("cli"),
            "devsynth.application.cli.commands": ModuleType("commands"),
            "devsynth.application.cli.commands.doctor_cmd": module,
        },
    ):
        func()
    assert called.get("flag")
