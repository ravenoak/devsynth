"""Streamlit WebUI implementation for DevSynth.

This module provides a graphical interface that mirrors the CLI workflows
through the :class:`~devsynth.interface.ux_bridge.UXBridge` abstraction.
The :class:`WebUI` exposes multiple pages available from a sidebar:

- **Project Onboarding** – initialize or onboard projects.
- **Requirements Gathering** – generate and inspect specifications.
- **Code Analysis** – analyze the project code base.
- **Synthesis Execution** – generate tests, code and run the pipeline.
- **Configuration Editing** – view or update settings.
- **EDRR Cycle** – execute a full Expand-Differentiate-Refine-Retrospect cycle.
- **Alignment** – check SDLC artifacts for traceability and consistency.
- **Alignment Metrics** – collect SDLC traceability metrics.
- **Inspect Config** – analyze and update project configuration.
- **Validate Manifest** – schema validation of project manifests.
- **Validate Metadata** – check Markdown front matter for consistency.
- **Test Metrics** – analyze commit history for test-first practices.
- **Generate Docs** – build API reference documentation.
- **Ingest Project** – run the ingestion pipeline.
- **API Spec** – generate API specifications.
- **Doctor** – quick diagnostics.
- **Diagnostics** – run detailed diagnostics.

All pages use collapsible sections and progress indicators to reflect the
UX guidance for clarity and responsiveness.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Sequence

import streamlit as st
from devsynth.application.cli import (
    code_cmd,
    config_cmd,
    init_cmd,
    inspect_cmd,
    run_pipeline_cmd,
    spec_cmd,
    test_cmd,
)
from devsynth.application.cli.commands.inspect_code_cmd import inspect_code_cmd
from devsynth.application.cli.commands.doctor_cmd import doctor_cmd
from devsynth.application.cli.commands.edrr_cycle_cmd import edrr_cycle_cmd
from devsynth.application.cli.commands.align_cmd import align_cmd
from devsynth.application.cli.commands.alignment_metrics_cmd import (
    alignment_metrics_cmd,
)
from devsynth.application.cli.commands.inspect_config_cmd import inspect_config_cmd
from devsynth.application.cli.commands.validate_manifest_cmd import (
    validate_manifest_cmd,
)
from devsynth.application.cli.commands.validate_metadata_cmd import (
    validate_metadata_cmd,
)
from devsynth.application.cli.commands.test_metrics_cmd import test_metrics_cmd
from devsynth.application.cli.commands.generate_docs_cmd import generate_docs_cmd
from devsynth.application.cli.ingest_cmd import ingest_cmd
from devsynth.application.cli.apispec import apispec_cmd
from devsynth.application.cli.setup_wizard import SetupWizard
from devsynth.config import load_project_config, save_config
from devsynth.domain.models.requirement import RequirementPriority, RequirementType
from devsynth.interface.ux_bridge import ProgressIndicator, UXBridge, sanitize_output


class WebUI(UXBridge):
    """Streamlit implementation of :class:`UXBridge` with navigation pages."""

    # ------------------------------------------------------------------
    # UXBridge API
    # ------------------------------------------------------------------
    def ask_question(
        self,
        message: str,
        *,
        choices: Optional[Sequence[str]] = None,
        default: Optional[str] = None,
        show_default: bool = True,
    ) -> str:
        if choices:
            index = 0
            if default in choices:
                index = list(choices).index(default)
            return st.selectbox(message, list(choices), index=index, key=message)
        return st.text_input(message, value=default or "", key=message)

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        return st.checkbox(message, value=default, key=message)

    def display_result(self, message: str, *, highlight: bool = False) -> None:
        message = sanitize_output(message)
        if highlight:
            st.markdown(f"**{message}**")
        else:
            st.write(message)

    class _UIProgress(ProgressIndicator):
        def __init__(self, total: int) -> None:
            self._bar = st.progress(0.0)
            self._total = total
            self._current = 0

        def update(
            self, *, advance: float = 1, description: Optional[str] = None
        ) -> None:
            self._current += advance
            self._bar.progress(min(1.0, self._current / self._total))

        def complete(self) -> None:
            self._bar.progress(1.0)

    def create_progress(
        self, description: str, *, total: int = 100
    ) -> ProgressIndicator:
        st.write(sanitize_output(description))
        return self._UIProgress(total)

    # ------------------------------------------------------------------
    # Page rendering helpers
    # ------------------------------------------------------------------
    def onboarding_page(self) -> None:
        """Render the onboarding page."""
        st.header("Project Onboarding")
        with st.expander("Initialize Project", expanded=True):
            with st.form("onboard"):
                path = st.text_input("Project Path", ".")
                project_root = st.text_input("Project Root", ".")
                language = st.text_input("Primary Language", "python")
                goals = st.text_input("Project Goals", "")
                submitted = st.form_submit_button("Initialize")
                if submitted:
                    with st.spinner("Initializing project..."):
                        init_cmd(
                            path=path,
                            project_root=project_root,
                            language=language,
                            goals=goals or None,
                            bridge=self,
                        )
            if st.button("Guided Setup", key="guided_setup"):
                with st.spinner("Starting guided setup..."):
                    SetupWizard(self).run()

    def requirements_page(self) -> None:
        """Render the requirements gathering page."""
        st.header("Requirements Gathering")
        with st.expander("Specification Generation", expanded=True):
            with st.form("requirements"):
                req_file = st.text_input("Requirements File", "requirements.md")
                submitted = st.form_submit_button("Generate Specs")
                if submitted:
                    with st.spinner("Generating specifications..."):
                        spec_cmd(requirements_file=req_file, bridge=self)
        st.divider()
        with st.expander("Inspect Requirements", expanded=True):
            with st.form("inspect"):
                input_file = st.text_input("Inspect File", "requirements.md")
                submitted = st.form_submit_button("Inspect Requirements")
                if submitted:
                    with st.spinner("Inspecting requirements..."):
                        inspect_cmd(
                            input_file=input_file, interactive=False, bridge=self
                        )
        st.divider()
        with st.expander("Specification Editor", expanded=True):
            spec_path = st.text_input("Specification File", "specs.md")
            if st.button("Load Spec", key="load_spec"):
                try:
                    with open(spec_path, "r", encoding="utf-8") as f:
                        st.session_state.spec_content = f.read()
                except FileNotFoundError:
                    st.session_state.spec_content = ""
            content = st.text_area(
                "Specification Content",
                st.session_state.get("spec_content", ""),
                height=300,
            )
            col1, col2 = st.columns(2)
            if col1.button("Save Spec", key="save_spec"):
                with open(spec_path, "w", encoding="utf-8") as f:
                    f.write(content)
                with st.spinner("Regenerating specifications..."):
                    spec_cmd(requirements_file=spec_path, bridge=self)
                st.session_state.spec_content = content
                st.markdown(content)
            if col2.button("Save Only", key="save_only"):
                with open(spec_path, "w", encoding="utf-8") as f:
                    f.write(content)
                st.session_state.spec_content = content
                st.markdown(content)
        st.divider()
        self._requirements_wizard()
        st.divider()
        self._gather_wizard()

    def _requirements_wizard(self) -> None:
        """Interactive requirements wizard using progress steps."""
        if "wizard_step" not in st.session_state:
            st.session_state.wizard_step = 0
            st.session_state.wizard_data = {
                "title": "",
                "description": "",
                "type": RequirementType.FUNCTIONAL.value,
                "priority": RequirementPriority.MEDIUM.value,
                "constraints": "",
            }

        steps = ["Title", "Description", "Type", "Priority", "Constraints"]
        step = st.session_state.wizard_step
        st.write(f"Step {step + 1} of {len(steps)}: {steps[step]}")
        st.progress((step + 1) / len(steps))
        data = st.session_state.wizard_data

        if step == 0:
            data["title"] = st.text_input("Requirement Title", data["title"])
        elif step == 1:
            data["description"] = st.text_area(
                "Requirement Description", data["description"]
            )
        elif step == 2:
            options = [t.value for t in RequirementType]
            index = options.index(data["type"])
            data["type"] = st.selectbox("Requirement Type", options, index=index)
        elif step == 3:
            options = [p.value for p in RequirementPriority]
            index = options.index(data["priority"])
            data["priority"] = st.selectbox(
                "Requirement Priority", options, index=index
            )
        elif step == 4:
            data["constraints"] = st.text_area(
                "Constraints (comma separated)", data["constraints"]
            )

        col1, col2 = st.columns(2)
        if col1.button("Back", disabled=step == 0):
            st.session_state.wizard_step = max(0, step - 1)
            return
        if col2.button("Next", disabled=step >= len(steps) - 1):
            st.session_state.wizard_step = min(len(steps) - 1, step + 1)
            return

        if step == len(steps) - 1 and st.button("Save Requirements"):
            result = {
                "title": data["title"],
                "description": data["description"],
                "type": data["type"],
                "priority": data["priority"],
                "constraints": [
                    c.strip() for c in data["constraints"].split(",") if c.strip()
                ],
            }
            with open("requirements_wizard.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            self.display_result(
                "[green]Requirements saved to requirements_wizard.json[/green]"
            )

    def _gather_wizard(self) -> None:
        """Run the requirements gathering workflow via :mod:`core.workflows`."""
        if st.button("Start Requirements Plan Wizard", key="g_start"):
            from devsynth.core.workflows import gather_requirements

            gather_requirements(self)

    def analysis_page(self) -> None:
        """Render the code analysis page."""
        st.header("Code Analysis")
        with st.expander("Inspect Code", expanded=True):
            with st.form("analysis"):
                path = st.text_input("Path", ".")
                submitted = st.form_submit_button("Inspect")
                if submitted:
                    with st.spinner("Inspecting code..."):
                        inspect_code_cmd(path=path)

    def synthesis_page(self) -> None:
        """Render the synthesis execution page."""
        st.header("Synthesis Execution")
        with st.expander("Generate Tests", expanded=True):
            with st.form("tests"):
                spec_file = st.text_input("Spec File", "specs.md")
                submitted = st.form_submit_button("Generate Tests")
                if submitted:
                    with st.spinner("Generating tests..."):
                        test_cmd(spec_file=spec_file, bridge=self)
        st.divider()
        with st.expander("Execute Code Generation", expanded=True):
            if st.button("Generate Code"):
                with st.spinner("Generating code..."):
                    code_cmd(bridge=self)
            if st.button("Run Pipeline"):
                with st.spinner("Running pipeline..."):
                    run_pipeline_cmd(bridge=self)

    def config_page(self) -> None:
        """Render the configuration editing page."""
        st.header("Configuration Editing")
        cfg = load_project_config()
        offline_toggle = st.toggle(
            "Offline Mode",
            value=cfg.config.offline_mode,
            key="offline_mode_toggle",
        )
        if st.button("Save Offline Mode", key="offline_mode_save"):
            cfg.config.offline_mode = offline_toggle
            with st.spinner("Saving configuration..."):
                save_config(
                    cfg.config,
                    use_pyproject=cfg.use_pyproject,
                    path=cfg.config.project_root,
                )
        with st.expander("Update Settings", expanded=True):
            with st.form("config"):
                key = st.text_input("Key")
                value = st.text_input("Value")
                submitted = st.form_submit_button("Update")
                if submitted:
                    with st.spinner("Updating configuration..."):
                        config_cmd(key=key or None, value=value or None, bridge=self)
        if st.button("View All Config"):
            with st.spinner("Loading configuration..."):
                config_cmd(bridge=self)

    def edrr_cycle_page(self) -> None:
        """Run an Expand-Differentiate-Refine-Retrospect cycle."""
        st.header("EDRR Cycle")
        with st.form("edrr_cycle"):
            manifest = self.ask_question("Manifest Path", default="manifest.yaml")
            auto = self.confirm_choice("Auto Progress", default=True)
            submitted = st.form_submit_button("Run Cycle")
        if submitted:
            with st.spinner("Running EDRR cycle..."):
                import sys

                module = sys.modules.get(
                    "devsynth.application.cli.commands.edrr_cycle_cmd"
                )
                if module is None:  # pragma: no cover - defensive fallback
                    import devsynth.application.cli.commands.edrr_cycle_cmd as module

                original = module.bridge
                module.bridge = self
                try:
                    module.edrr_cycle_cmd(manifest=manifest, auto=auto)
                finally:
                    module.bridge = original

    def alignment_page(self) -> None:
        """Check SDLC alignment between artifacts."""
        st.header("Alignment")
        with st.form("alignment"):
            path = self.ask_question("Project Path", default=".")
            verbose = self.confirm_choice("Verbose Output", default=False)
            submitted = st.form_submit_button("Check Alignment")
        if submitted:
            with st.spinner("Checking alignment..."):
                import sys

                module = sys.modules.get("devsynth.application.cli.commands.align_cmd")
                if module is None:  # pragma: no cover - defensive fallback
                    import devsynth.application.cli.commands.align_cmd as module

                original = module.bridge
                module.bridge = self
                try:
                    module.align_cmd(path=path, verbose=verbose)
                finally:
                    module.bridge = original

    def alignment_metrics_page(self) -> None:
        """Collect and display alignment metrics."""
        st.header("Alignment Metrics")
        with st.form("alignment_metrics"):
            path = self.ask_question("Project Path", default=".")
            metrics_file = self.ask_question(
                "Metrics File", default=".devsynth/alignment_metrics.json"
            )
            output = st.text_input("Report File", "")
            submitted = st.form_submit_button("Collect Metrics")
        if submitted:
            with st.spinner("Collecting metrics..."):
                import sys

                module = sys.modules.get(
                    "devsynth.application.cli.commands.alignment_metrics_cmd"
                )
                if module is None:  # pragma: no cover - defensive fallback
                    import devsynth.application.cli.commands.alignment_metrics_cmd as module

                original = module.bridge
                module.bridge = self
                try:
                    module.alignment_metrics_cmd(
                        path=path,
                        metrics_file=metrics_file,
                        output=output or None,
                    )
                finally:
                    module.bridge = original

    def inspect_config_page(self) -> None:
        """Analyze and optionally update the project configuration."""
        st.header("Inspect Config")
        with st.form("inspect_config"):
            path = self.ask_question("Project Path", default=".")
            update = self.confirm_choice("Update", default=False)
            prune = self.confirm_choice("Prune", default=False)
            submitted = st.form_submit_button("Inspect Config")
        if submitted:
            with st.spinner("Inspecting configuration..."):
                import sys

                module = sys.modules.get(
                    "devsynth.application.cli.commands.inspect_config_cmd"
                )
                if module is None:  # pragma: no cover - defensive fallback
                    import devsynth.application.cli.commands.inspect_config_cmd as module

                original = module.bridge
                module.bridge = self
                try:
                    module.inspect_config_cmd(
                        path=path,
                        update=update,
                        prune=prune,
                    )
                finally:
                    module.bridge = original

    def validate_manifest_page(self) -> None:
        """Validate the project manifest against its schema."""
        st.header("Validate Manifest")
        with st.form("validate_manifest"):
            manifest_path = st.text_input("Manifest Path", "manifest.yaml")
            schema_path = st.text_input("Schema Path", "")
            submitted = st.form_submit_button("Validate Manifest")
        if submitted:
            with st.spinner("Validating manifest..."):
                import sys

                module = sys.modules.get(
                    "devsynth.application.cli.commands.validate_manifest_cmd"
                )
                if module is None:  # pragma: no cover - defensive fallback
                    import devsynth.application.cli.commands.validate_manifest_cmd as module

                original = module.bridge
                module.bridge = self
                try:
                    module.validate_manifest_cmd(
                        manifest_path=manifest_path or None,
                        schema_path=schema_path or None,
                    )
                finally:
                    module.bridge = original

    def validate_metadata_page(self) -> None:
        """Validate Markdown front-matter metadata."""
        st.header("Validate Metadata")
        with st.form("validate_metadata"):
            directory = st.text_input("Docs Directory", "docs")
            file = st.text_input("Single File", "")
            verbose = self.confirm_choice("Verbose Output", default=False)
            submitted = st.form_submit_button("Validate Metadata")
        if submitted:
            with st.spinner("Validating metadata..."):
                import sys

                module = sys.modules.get(
                    "devsynth.application.cli.commands.validate_metadata_cmd"
                )
                if module is None:  # pragma: no cover - defensive fallback
                    import devsynth.application.cli.commands.validate_metadata_cmd as module

                original = module.bridge
                module.bridge = self
                try:
                    module.validate_metadata_cmd(
                        directory=directory or None,
                        file=file or None,
                        verbose=verbose,
                    )
                finally:
                    module.bridge = original

    def test_metrics_page(self) -> None:
        """Analyze test-first development metrics."""
        st.header("Test Metrics")
        with st.form("test_metrics"):
            days = st.number_input("Days", min_value=1, step=1, value=30)
            output_file = st.text_input("Output File", "")
            submitted = st.form_submit_button("Analyze Metrics")
        if submitted:
            with st.spinner("Analyzing metrics..."):
                import sys

                module = sys.modules.get(
                    "devsynth.application.cli.commands.test_metrics_cmd"
                )
                if module is None:  # pragma: no cover - defensive fallback
                    import devsynth.application.cli.commands.test_metrics_cmd as module

                original = module.bridge
                module.bridge = self
                try:
                    module.test_metrics_cmd(
                        days=int(days), output_file=output_file or None
                    )
                finally:
                    module.bridge = original

    def docs_generation_page(self) -> None:
        """Generate API reference documentation."""
        st.header("Generate Docs")
        with st.form("generate_docs"):
            path = st.text_input("Project Path", ".")
            output_dir = st.text_input("Output Directory", "")
            submitted = st.form_submit_button("Generate Docs")
        if submitted:
            with st.spinner("Generating documentation..."):
                import sys

                module = sys.modules.get(
                    "devsynth.application.cli.commands.generate_docs_cmd"
                )
                if module is None:  # pragma: no cover - defensive fallback
                    import devsynth.application.cli.commands.generate_docs_cmd as module

                original = module.bridge
                module.bridge = self
                try:
                    module.generate_docs_cmd(
                        path=path or None,
                        output_dir=output_dir or None,
                    )
                finally:
                    module.bridge = original

    def ingestion_page(self) -> None:
        """Run the ingestion pipeline."""
        st.header("Ingest Project")
        with st.form("ingest"):
            manifest_path = st.text_input("Manifest Path", "manifest.yaml")
            dry_run = self.confirm_choice("Dry Run", default=False)
            verbose = self.confirm_choice("Verbose Output", default=False)
            validate_only = self.confirm_choice("Validate Only", default=False)
            submitted = st.form_submit_button("Ingest Project")
        if submitted:
            with st.spinner("Running ingestion..."):
                import sys

                module = sys.modules.get("devsynth.application.cli.ingest_cmd")
                if module is None:  # pragma: no cover - defensive fallback
                    import devsynth.application.cli.ingest_cmd as module

                original = module.bridge
                module.bridge = self
                try:
                    module.ingest_cmd(
                        manifest_path=manifest_path or None,
                        dry_run=dry_run,
                        verbose=verbose,
                        validate_only=validate_only,
                    )
                finally:
                    module.bridge = original

    def apispec_page(self) -> None:
        """Generate an API specification."""
        st.header("API Spec")
        with st.form("apispec"):
            api_type = st.selectbox("API Type", ("rest", "graphql", "grpc"))
            format_type = st.text_input("Format", "openapi")
            name = st.text_input("Name", "api")
            path = st.text_input("Path", ".")
            submitted = st.form_submit_button("Generate Spec")
        if submitted:
            with st.spinner("Generating API spec..."):
                import sys

                module = sys.modules.get("devsynth.application.cli.apispec")
                if module is None:  # pragma: no cover - defensive fallback
                    import devsynth.application.cli.apispec as module

                original = module.bridge
                module.bridge = self
                try:
                    module.apispec_cmd(
                        api_type=api_type,
                        format_type=format_type,
                        name=name,
                        path=path,
                    )
                finally:
                    module.bridge = original

    def doctor_page(self) -> None:
        """Render the doctor diagnostics page."""
        st.header("Doctor")
        with st.spinner("Validating configuration..."):
            import sys

            doc_module = sys.modules.get(
                "devsynth.application.cli.commands.doctor_cmd"
            )
            if doc_module is None:  # pragma: no cover - defensive fallback
                import devsynth.application.cli.commands.doctor_cmd as doc_module

            original = doc_module.bridge
            doc_module.bridge = self
            try:
                doc_module.doctor_cmd()
            finally:
                doc_module.bridge = original

    def diagnostics_page(self) -> None:
        """Run environment diagnostics via :func:`doctor_cmd`."""
        st.header("Diagnostics")
        with st.form("diagnostics"):
            config_dir = st.text_input("Config Directory", "config")
            submitted = st.form_submit_button("Run Diagnostics")
        if submitted:
            with st.spinner("Running diagnostics..."):
                import sys

                doc_module = sys.modules.get(
                    "devsynth.application.cli.commands.doctor_cmd"
                )
                if doc_module is None:  # pragma: no cover - defensive fallback
                    import devsynth.application.cli.commands.doctor_cmd as doc_module

                original = doc_module.bridge
                doc_module.bridge = self
                try:
                    doc_module.doctor_cmd(config_dir)
                finally:
                    doc_module.bridge = original

    # ------------------------------------------------------------------
    # Application entry point
    # ------------------------------------------------------------------
    def run(self) -> None:
        """Run the Streamlit application."""
        st.set_page_config(page_title="DevSynth WebUI", layout="wide")
        st.sidebar.title("DevSynth")
        nav = st.sidebar.radio(
            "Navigation",
            (
                "Onboarding",
                "Requirements",
                "Analysis",
                "Synthesis",
                "EDRR Cycle",
                "Alignment",
                "Alignment Metrics",
                "Inspect Config",
                "Validate Manifest",
                "Validate Metadata",
                "Test Metrics",
                "Generate Docs",
                "Ingest",
                "API Spec",
                "Config",
                "Doctor",
                "Diagnostics",
            ),
        )
        if nav == "Onboarding":
            self.onboarding_page()
        elif nav == "Requirements":
            self.requirements_page()
        elif nav == "Analysis":
            self.analysis_page()
        elif nav == "Synthesis":
            self.synthesis_page()
        elif nav == "EDRR Cycle":
            self.edrr_cycle_page()
        elif nav == "Alignment":
            self.alignment_page()
        elif nav == "Alignment Metrics":
            self.alignment_metrics_page()
        elif nav == "Inspect Config":
            self.inspect_config_page()
        elif nav == "Validate Manifest":
            self.validate_manifest_page()
        elif nav == "Validate Metadata":
            self.validate_metadata_page()
        elif nav == "Test Metrics":
            self.test_metrics_page()
        elif nav == "Generate Docs":
            self.docs_generation_page()
        elif nav == "Ingest":
            self.ingestion_page()
        elif nav == "API Spec":
            self.apispec_page()
        elif nav == "Config":
            self.config_page()
        elif nav == "Doctor":
            self.doctor_page()
        elif nav == "Diagnostics":
            self.diagnostics_page()


def run() -> None:
    """Convenience entry point for ``streamlit run`` or the CLI."""
    WebUI().run()


# Backwards compatibility with older docs
run_webui = run


__all__ = ["WebUI", "run"]


if __name__ == "__main__":  # pragma: no cover - manual invocation
    run()
