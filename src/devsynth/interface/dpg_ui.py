"""Dear PyGUI based interface for DevSynth workflows.

This module wires the :class:`DearPyGUIBridge` into a minimal window
providing quick access to common DevSynth CLI workflows.  Each button
invokes the corresponding workflow function through the bridge which
ensures consistent user interaction behaviour across interfaces.
"""

from __future__ import annotations

import json
from collections.abc import Callable

try:  # pragma: no cover - optional dependency
    import dearpygui.dearpygui as dpg
except Exception:  # pragma: no cover - defensive
    dpg = None  # type: ignore

from devsynth.domain.models.requirement import RequirementPriority, RequirementType

from .dpg_bridge import DearPyGUIBridge


def _bind(
    cmd: Callable[[DearPyGUIBridge], None], bridge: DearPyGUIBridge
) -> Callable[[], None]:
    """Return a callback that executes *cmd* with a progress indicator."""

    def _callback() -> None:
        def _pulse(progress) -> None:
            progress.update(advance=5)
            if getattr(progress, "_current", 0) >= getattr(progress, "_total", 100):
                progress._current = 0

        bridge.run_cli_command(cmd, progress_hook=_pulse)

    return _callback


def _requirements_wizard_dialog(bridge: DearPyGUIBridge) -> None:
    """Interactive requirements wizard displayed via modal dialogs.

    This implementation mirrors the WebUI requirements wizard by providing
    step-based progress information and graceful error handling. Collected
    requirements are written to ``requirements_wizard.json``.
    """

    steps = [
        (
            "title",
            "Requirement Title",
            None,
            "",
        ),
        (
            "description",
            "Requirement Description",
            None,
            "",
        ),
        (
            "type",
            "Requirement Type",
            [t.value for t in RequirementType],
            RequirementType.FUNCTIONAL.value,
        ),
        (
            "priority",
            "Requirement Priority",
            [p.value for p in RequirementPriority],
            RequirementPriority.MEDIUM.value,
        ),
        (
            "constraints",
            "Constraints (comma separated, optional)",
            None,
            "",
        ),
    ]

    step_names = ["Title", "Description", "Type", "Priority", "Constraints"]
    responses: dict[str, str] = {}
    progress = bridge.create_progress("Requirements Wizard", total=len(steps))

    index = 0
    try:
        while index < len(steps):
            key, message, choices, default = steps[index]
            progress.update(
                description=f"Step {index + 1}/{len(steps)}: {step_names[index]}",
                advance=0,
            )
            reply = bridge.ask_question(
                message + " (type 'back' to go back)",
                choices=choices,
                default=responses.get(key, default),
            )
            if reply.lower() == "back":
                if index > 0:
                    index -= 1
                    progress.update(
                        description=f"Step {index + 1}/{len(steps)}: {step_names[index]}",
                        advance=-1,
                    )
                else:
                    bridge.display_result("[yellow]Already at first step.[/yellow]")
                continue
            responses[key] = reply
            index += 1
            progress.update(advance=1)

        result = {
            "title": responses.get("title", ""),
            "description": responses.get("description", ""),
            "type": responses.get("type", RequirementType.FUNCTIONAL.value),
            "priority": responses.get("priority", RequirementPriority.MEDIUM.value),
            "constraints": [
                c.strip()
                for c in responses.get("constraints", "").split(",")
                if c.strip()
            ],
        }

        with open("requirements_wizard.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        bridge.display_result(
            "[green]Requirements saved to requirements_wizard.json[/green]"
        )
    except Exception as exc:  # pragma: no cover - defensive
        bridge.display_result(
            f"[red]ERROR in requirements wizard: {exc}[/red]",
            message_type="error",
        )
    finally:
        progress.complete()


def run() -> None:
    """Launch the Dear PyGUI interface."""
    if dpg is None:  # pragma: no cover - defensive
        raise RuntimeError("dearpygui is required for the DPG interface")

    bridge = DearPyGUIBridge()

    # Import workflow commands lazily to avoid heavy dependencies at import time
    from devsynth.application.cli import (
        check_cmd,
        code_cmd,
        config_cmd,
        dbschema_cmd,
        doctor_cmd,
        edrr_cycle_cmd,
        enable_feature_cmd,
        gather_cmd,
        ingest_cmd,
        init_cmd,
        inspect_cmd,
        inspect_code_cmd,
        refactor_cmd,
        run_pipeline_cmd,
        serve_cmd,
        spec_cmd,
        test_cmd,
        webapp_cmd,
        webui_cmd,
    )
    from devsynth.application.cli.apispec import apispec_cmd
    from devsynth.application.cli.commands import (
        align_cmd,
        alignment_metrics_cmd,
        generate_docs_cmd,
        inspect_config_cmd,
        test_metrics_cmd,
        validate_manifest_cmd,
        validate_metadata_cmd,
    )

    def _enable_feature(*, bridge: DearPyGUIBridge) -> None:
        name = bridge.ask_question("Feature to enable:")
        if name:
            enable_feature_cmd(name, bridge=bridge)

    with dpg.window(label="DevSynth", tag="__primary_window"):
        dpg.add_button(label="Init", callback=_bind(init_cmd, bridge))
        dpg.add_button(label="Gather", callback=_bind(gather_cmd, bridge))
        dpg.add_button(label="Inspect", callback=_bind(inspect_cmd, bridge))
        dpg.add_button(label="Spec", callback=_bind(spec_cmd, bridge))
        dpg.add_button(label="Test", callback=_bind(test_cmd, bridge))
        dpg.add_button(label="Code", callback=_bind(code_cmd, bridge))
        dpg.add_button(label="Run Pipeline", callback=_bind(run_pipeline_cmd, bridge))
        dpg.add_button(label="Config", callback=_bind(config_cmd, bridge))
        dpg.add_button(label="Enable Feature", callback=_bind(_enable_feature, bridge))
        dpg.add_button(
            label="Wizard", callback=lambda: _requirements_wizard_dialog(bridge)
        )
        dpg.add_button(label="Inspect Code", callback=_bind(inspect_code_cmd, bridge))
        dpg.add_button(label="Refactor", callback=_bind(refactor_cmd, bridge))
        dpg.add_button(label="Webapp", callback=_bind(webapp_cmd, bridge))
        dpg.add_button(label="Serve", callback=_bind(serve_cmd, bridge))
        dpg.add_button(label="DbSchema", callback=_bind(dbschema_cmd, bridge))
        dpg.add_button(label="Doctor", callback=_bind(doctor_cmd, bridge))
        dpg.add_button(label="Check", callback=_bind(check_cmd, bridge))
        dpg.add_button(label="EDRR Cycle", callback=_bind(edrr_cycle_cmd, bridge))
        dpg.add_button(label="Align", callback=_bind(align_cmd, bridge))
        dpg.add_button(
            label="Alignment Metrics",
            callback=_bind(alignment_metrics_cmd, bridge),
        )
        dpg.add_button(
            label="Inspect Config", callback=_bind(inspect_config_cmd, bridge)
        )
        dpg.add_button(
            label="Validate Manifest",
            callback=_bind(validate_manifest_cmd, bridge),
        )
        dpg.add_button(
            label="Validate Metadata",
            callback=_bind(validate_metadata_cmd, bridge),
        )
        dpg.add_button(label="Test Metrics", callback=_bind(test_metrics_cmd, bridge))
        dpg.add_button(label="Generate Docs", callback=_bind(generate_docs_cmd, bridge))
        dpg.add_button(label="Ingest", callback=_bind(ingest_cmd, bridge))
        dpg.add_button(label="API Spec", callback=_bind(apispec_cmd, bridge))
        dpg.add_button(label="WebUI", callback=_bind(webui_cmd, bridge))

    dpg.set_primary_window("__primary_window", True)
    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()

    dpg.destroy_context()


__all__ = ["run"]
