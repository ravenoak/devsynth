"""Generate tests based on specifications."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pytest
from rich.console import Console
from rich.table import Table

from devsynth.core.workflows import filter_args, generate_tests
from devsynth.interface.ux_bridge import UXBridge

from ..utils import (
    _check_services,
    _env_flag,
    _handle_error,
    _resolve_bridge,
    _validate_file_path,
)
from .spec_cmd import spec_cmd


@pytest.mark.fast
def test_cmd(
    spec_file: str = "specs.md",
    *,
    auto_confirm: bool | None = None,
    bridge: UXBridge | None = None,
) -> None:
    """Generate tests based on specifications.

    This command analyzes a specifications file and generates test cases
    that can be used to validate the implementation.

    Args:
        spec_file: Path to the specifications file (Markdown format)
        bridge: Optional UX bridge for interaction

    Examples:
        Generate tests from the default specifications file:
        ```
        devsynth test
        ```

        Generate tests from a custom specifications file:
        ```
        devsynth test --spec-file custom_specs.md
        ```
    """

    console = Console()
    bridge = _resolve_bridge(bridge)
    auto_confirm = (
        _env_flag("DEVSYNTH_AUTO_CONFIRM") if auto_confirm is None else auto_confirm
    )
    try:
        # Check required services
        if not _check_services(bridge):
            return

        # Validate input file
        error = _validate_file_path(spec_file)
        if error:
            bridge.display_result(f"[yellow]{error}[/yellow]")
            if auto_confirm or bridge.confirm_choice(
                f"Run 'devsynth spec' to generate {spec_file}?", default=True
            ):
                spec_cmd(bridge=bridge, auto_confirm=auto_confirm)
            else:
                return

        # Simple progress indicator with four logical steps
        steps = [
            "Analyzing specifications",
            "Identifying test cases",
            "Generating tests",
            "Finishing",
        ]
        progress = bridge.create_progress("Generating tests", total=len(steps))

        try:
            progress.update(description=steps[0])
            args = filter_args({"spec_file": spec_file})

            progress.update(description=steps[1])

            progress.update(description=steps[2])
            result = generate_tests(**args)

            progress.update(description=steps[3])
        finally:
            progress.complete()

        result = result if isinstance(result, dict) else {}

        # Handle result
        if result.get("success"):
            output_dir = result.get("output_dir", "tests")

            # Create a summary table of what was generated
            summary_table = Table(title="Test Generation Summary")
            summary_table.add_column("Test Type", style="cyan")
            summary_table.add_column("Location", style="blue")

            # Add rows for each test type
            test_types = {
                "Unit Tests": f"{output_dir}/unit",
                "Integration Tests": f"{output_dir}/integration",
                "Behavior Tests": f"{output_dir}/behavior",
            }

            for test_type, location in test_types.items():
                summary_table.add_row(test_type, location)

            console.print(summary_table)

            bridge.display_result(
                f"[green]Tests successfully generated from {spec_file}.[/green]",
                highlight=True,
            )

            # Show next steps
            bridge.display_result("\n[bold]Next Steps:[/bold]")
            bridge.display_result("1. Review the generated tests")
            bridge.display_result("2. Generate code: devsynth code")
            bridge.display_result("3. Run tests: devsynth run-pipeline")
        else:
            _handle_error(bridge, result)
    except Exception as err:  # pragma: no cover - defensive
        _handle_error(bridge, err)


__all__ = ["test_cmd"]
