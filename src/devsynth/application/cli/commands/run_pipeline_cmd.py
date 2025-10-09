"""Execute generated code or specific targets."""

from __future__ import annotations

import json
from typing import Annotated, Optional, cast

import typer

from devsynth.core import workflows
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger

from ..ingest_models import JSONValue, PipelineReport
from ..utils import _check_services, _env_flag, _handle_error, _resolve_bridge


def _parse_report(value: Optional[str]) -> Optional[PipelineReport]:
    """Parse report data from JSON string."""

    if not value:
        return None
    try:
        data = json.loads(value)
        if isinstance(data, dict):
            return cast(PipelineReport, data)
    except json.JSONDecodeError:
        logger.warning("Invalid report JSON provided: %s", value)
    return None


def run_pipeline_cmd(
    target: Optional[str] = None,
    report: Optional[str] = typer.Option(
        None, "--report", help="JSON string with additional report data"
    ),
    *,
    auto_confirm: Optional[bool] = None,
    bridge: Optional[UXBridge] = typer.Option(None, hidden=True),
) -> None:
    """Run the generated code or a specific target.

    This command executes the generated code or a specific target, such as unit tests.
    It can also persist a report with the results.

    Args:
        target: Execution target (e.g. "unit-tests", "integration-tests", "all")
        report: JSON string with report data to persist with pipeline results
        bridge: Optional UX bridge for interaction

    Examples:
        Run the default pipeline:
        ```
        devsynth run-pipeline
        ```

        Run a specific target:
        ```
        devsynth run-pipeline --target unit-tests
        ```
    """

    bridge = _resolve_bridge(bridge if isinstance(bridge, UXBridge) else None)
    auto_confirm = (
        _env_flag("DEVSYNTH_AUTO_CONFIRM") if auto_confirm is None else auto_confirm
    )
    try:
        # Check required services
        if not _check_services(bridge):
            return

        # Validate target if provided
        valid_targets = ["unit-tests", "integration-tests", "behavior-tests", "all"]
        if target and target not in valid_targets:
            bridge.display_result(
                (
                    "[yellow]Warning: '"
                    + str(target)
                    + "' is not a standard target. Valid targets are: "
                    + ", ".join(valid_targets)
                    + "[/yellow]"
                )
            )
            if not (
                auto_confirm
                or bridge.confirm_choice(
                    f"Continue with target '{target}'?", default=True
                )
            ):
                return

        # Execute command
        running_label = "target: " + str(target) if target else "default pipeline"
        bridge.display_result("[blue]Running " + running_label + "...[/blue]")
        parsed_report = _parse_report(report)
        command_payload: dict[str, JSONValue | None] = {
            "target": target,
            "report": parsed_report,
        }
        result = workflows.execute_command("run-pipeline", command_payload)

        # Handle result
        if result.get("success"):
            if target:
                bridge.display_result(
                    f"[green]Successfully executed target: {target}[/green]"
                )
            else:
                bridge.display_result("[green]Pipeline execution complete.[/green]")

            # Display additional result information if available
            if "output" in result:
                bridge.display_result(f"[blue]Output:[/blue]\n{result['output']}")
        else:
            _handle_error(bridge, result)
    except Exception as err:  # pragma: no cover - defensive
        _handle_error(bridge, err)


logger = DevSynthLogger(__name__)


__all__ = ["run_pipeline_cmd"]
