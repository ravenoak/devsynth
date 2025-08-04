"""Dear PyGUI based interface for DevSynth workflows.

This module wires the :class:`DearPyGUIBridge` into a minimal window
providing quick access to common DevSynth CLI workflows.  Each button
invokes the corresponding workflow function through the bridge which
ensures consistent user interaction behaviour across interfaces.
"""

from __future__ import annotations

from typing import Callable
import threading
import time

try:  # pragma: no cover - optional dependency
    import dearpygui.dearpygui as dpg
except Exception:  # pragma: no cover - defensive
    dpg = None  # type: ignore

from .dpg_bridge import DearPyGUIBridge


def _bind(
    cmd: Callable[[DearPyGUIBridge], None], bridge: DearPyGUIBridge
) -> Callable[[], None]:
    """Return a callback that executes *cmd* with a progress indicator."""

    def _callback() -> None:
        progress = bridge.create_progress(f"Running {cmd.__name__}")
        done = threading.Event()

        def _run() -> None:
            try:
                cmd(bridge=bridge)
            finally:
                done.set()

        def _pulse() -> None:
            while not done.is_set():
                progress.update(advance=5)
                if getattr(progress, "_current", 0) >= getattr(progress, "_total", 100):
                    progress._current = 0
                time.sleep(0.1)
            progress.complete()

        threading.Thread(target=_run, daemon=True).start()
        threading.Thread(target=_pulse, daemon=True).start()

    return _callback


def run() -> None:
    """Launch the Dear PyGUI interface."""
    if dpg is None:  # pragma: no cover - defensive
        raise RuntimeError("dearpygui is required for the DPG interface")

    bridge = DearPyGUIBridge()

    # Import workflow commands lazily to avoid heavy dependencies at import time
    from devsynth.application.cli import (
        init_cmd,
        gather_cmd,
        inspect_cmd,
        spec_cmd,
        test_cmd,
        code_cmd,
        run_pipeline_cmd,
        config_cmd,
        enable_feature_cmd,
        refactor_cmd,
        webapp_cmd,
        serve_cmd,
        dbschema_cmd,
        doctor_cmd,
        check_cmd,
        webui_cmd,
        inspect_code_cmd,
        edrr_cycle_cmd,
        ingest_cmd,
    )
    from devsynth.application.cli.apispec import apispec_cmd
    from devsynth.application.cli.requirements_commands import wizard_cmd
    from devsynth.application.cli.commands import (
        align_cmd,
        alignment_metrics_cmd,
        inspect_config_cmd,
        validate_manifest_cmd,
        validate_metadata_cmd,
        test_metrics_cmd,
        generate_docs_cmd,
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
        dpg.add_button(label="Wizard", callback=_bind(wizard_cmd, bridge))
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
