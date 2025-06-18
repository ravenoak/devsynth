"""Streamlit WebUI implementation for DevSynth.

This module provides a minimal Streamlit based graphical interface that
leverages the existing CLI workflows through the :class:`UXBridge`
interface. The WebUI exposes five main sections via a sidebar
navigation menu:

- **Project Onboarding**: initialize or onboard an existing project.
- **Requirements Gathering**: inspect requirements and generate
  specifications.
- **Code Analysis**: analyze the current project state.
- **Synthesis Execution**: generate tests, code, and run the
  pipeline.
- **Configuration Editing**: view or update project settings.

Each section uses forms and progress indicators to mirror the CLI
experience.
"""

from __future__ import annotations

from typing import Optional, Sequence

import streamlit as st

from devsynth.interface.ux_bridge import UXBridge
from devsynth.application.cli import (
    init_cmd,
    spec_cmd,
    test_cmd,
    code_cmd,
    run_pipeline_cmd,
    config_cmd,
    inspect_cmd,
)
from devsynth.application.cli.commands.analyze_code_cmd import analyze_code_cmd


class WebUIUXBridge(UXBridge):
    """Streamlit implementation of :class:`UXBridge`."""

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
        if highlight:
            st.markdown(f"**{message}**")
        else:
            st.write(message)


def _onboarding(bridge: WebUIUXBridge) -> None:
    st.header("Project Onboarding")
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
                    bridge=bridge,
                )


def _requirements(bridge: WebUIUXBridge) -> None:
    st.header("Requirements Gathering")
    with st.form("requirements"):
        req_file = st.text_input("Requirements File", "requirements.md")
        submitted = st.form_submit_button("Generate Specs")
        if submitted:
            with st.spinner("Generating specifications..."):
                spec_cmd(requirements_file=req_file, bridge=bridge)
    st.divider()
    with st.form("inspect"):
        input_file = st.text_input("Inspect File", "requirements.md")
        submitted = st.form_submit_button("Inspect Requirements")
        if submitted:
            with st.spinner("Inspecting requirements..."):
                inspect_cmd(input_file=input_file, interactive=False, bridge=bridge)


def _analysis() -> None:
    st.header("Code Analysis")
    with st.form("analysis"):
        path = st.text_input("Path", ".")
        submitted = st.form_submit_button("Analyze")
        if submitted:
            with st.spinner("Analyzing code..."):
                analyze_code_cmd(path=path)


def _synthesis(bridge: WebUIUXBridge) -> None:
    st.header("Synthesis Execution")
    with st.form("tests"):
        spec_file = st.text_input("Spec File", "specs.md")
        submitted = st.form_submit_button("Generate Tests")
        if submitted:
            with st.spinner("Generating tests..."):
                test_cmd(spec_file=spec_file, bridge=bridge)
    st.divider()
    if st.button("Generate Code"):
        with st.spinner("Generating code..."):
            code_cmd(bridge=bridge)
    if st.button("Run Pipeline"):
        with st.spinner("Running pipeline..."):
            run_pipeline_cmd(bridge=bridge)


def _config(bridge: WebUIUXBridge) -> None:
    st.header("Configuration Editing")
    with st.form("config"):
        key = st.text_input("Key")
        value = st.text_input("Value")
        submitted = st.form_submit_button("Update")
        if submitted:
            with st.spinner("Updating configuration..."):
                config_cmd(key=key or None, value=value or None, bridge=bridge)
    if st.button("View All Config"):
        with st.spinner("Loading configuration..."):
            config_cmd(bridge=bridge)


def run_webui() -> None:
    """Entry point for the Streamlit application."""

    st.set_page_config(page_title="DevSynth WebUI", layout="wide")
    bridge = WebUIUXBridge()

    st.sidebar.title("DevSynth")
    nav = st.sidebar.radio(
        "Navigation",
        (
            "Onboarding",
            "Requirements",
            "Analysis",
            "Synthesis",
            "Config",
        ),
    )

    if nav == "Onboarding":
        _onboarding(bridge)
    elif nav == "Requirements":
        _requirements(bridge)
    elif nav == "Analysis":
        _analysis()
    elif nav == "Synthesis":
        _synthesis(bridge)
    elif nav == "Config":
        _config(bridge)


if __name__ == "__main__":  # pragma: no cover - manual execution
    run_webui()

WebUI = WebUIUXBridge  # Backwards compatibility

__all__ = ["WebUIUXBridge", "WebUI", "run_webui"]
