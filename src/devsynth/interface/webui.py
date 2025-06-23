"""Streamlit WebUI implementation for DevSynth.

This module provides a graphical interface that mirrors the CLI workflows
through the :class:`~devsynth.interface.ux_bridge.UXBridge` abstraction.
The :class:`WebUI` exposes five pages available from a sidebar:

- **Project Onboarding** – initialize or onboard projects.
- **Requirements Gathering** – generate and inspect specifications.
- **Code Analysis** – analyze the project code base.
- **Synthesis Execution** – generate tests, code and run the pipeline.
- **Configuration Editing** – view or update settings.

All pages use collapsible sections and progress indicators to reflect the
UX guidance for clarity and responsiveness.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Sequence

import streamlit as st
import yaml

from devsynth.application.cli import (
    code_cmd,
    config_cmd,
    init_cmd,
    inspect_cmd,
    run_pipeline_cmd,
    spec_cmd,
    test_cmd,
)
from devsynth.application.cli.commands.analyze_code_cmd import analyze_code_cmd
from devsynth.application.cli.commands.doctor_cmd import doctor_cmd
from devsynth.config import get_project_config, save_config
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
            if st.button("Save Spec", key="save_spec"):
                with open(spec_path, "w", encoding="utf-8") as f:
                    f.write(content)
                with st.spinner("Regenerating specifications..."):
                    spec_cmd(requirements_file=spec_path, bridge=self)
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
        with st.expander("Analyze Code", expanded=True):
            with st.form("analysis"):
                path = st.text_input("Path", ".")
                submitted = st.form_submit_button("Analyze")
                if submitted:
                    with st.spinner("Analyzing code..."):
                        analyze_code_cmd(path=path)

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

    def doctor_page(self) -> None:
        """Render the doctor diagnostics page."""
        st.header("Doctor")
        with st.spinner("Validating configuration..."):
            doctor_cmd()

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
                "Config",
                "Doctor",
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
        elif nav == "Config":
            self.config_page()
        elif nav == "Doctor":
            self.doctor_page()


def run() -> None:
    """Convenience entry point for ``streamlit run`` or the CLI."""
    WebUI().run()


# Backwards compatibility with older docs
run_webui = run


__all__ = ["WebUI", "run"]


if __name__ == "__main__":  # pragma: no cover - manual invocation
    run()
