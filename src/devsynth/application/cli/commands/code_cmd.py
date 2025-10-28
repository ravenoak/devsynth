"""Generate implementation code from tests."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from devsynth.core.workflows import generate_code
from devsynth.interface.ux_bridge import UXBridge

from ..utils import _check_services, _env_flag, _handle_error, _resolve_bridge
from .test_cmd import test_cmd


def code_cmd(
    *, auto_confirm: bool | None = None, bridge: UXBridge | None = None
) -> None:
    """Generate implementation code from tests.

    This command analyzes the test files and generates implementation code
    that satisfies the test requirements.

    Args:
        bridge: Optional UX bridge for interaction

    Examples:
        Generate implementation code:
        ```
        devsynth code
        ```
    """

    bridge = _resolve_bridge(bridge)
    auto_confirm = (
        _env_flag("DEVSYNTH_AUTO_CONFIRM") if auto_confirm is None else auto_confirm
    )
    try:
        # Check required services
        if not _check_services(bridge):
            return

        # Check if tests directory exists
        tests_dir = Path("tests")
        if not tests_dir.exists() or not any(tests_dir.iterdir()):
            bridge.display_result(
                "[yellow]No tests found in 'tests' directory.[/yellow]"
            )
            if auto_confirm or bridge.confirm_choice(
                "Run 'devsynth test' to generate tests?", default=True
            ):
                test_cmd(bridge=bridge, auto_confirm=auto_confirm)
            else:
                return

        # Generate code
        bridge.display_result(
            "[blue]Generating implementation code from tests...[/blue]"
        )
        result = generate_code()

        # Handle result
        if result.get("success"):
            output_dir = result.get("output_dir", "src")
            bridge.display_result("[green]Code generated successfully.[/green]")
            bridge.display_result(f"[blue]Code saved to directory: {output_dir}[/blue]")
        else:
            _handle_error(bridge, result)
    except Exception as err:  # pragma: no cover - defensive
        _handle_error(bridge, err)


__all__ = ["code_cmd"]
