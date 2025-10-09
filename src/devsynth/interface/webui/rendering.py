from __future__ import annotations

import importlib
import json
import os
import time
from collections.abc import Callable, Mapping, Sequence
from contextlib import ExitStack
from pathlib import Path
from typing import Any

from devsynth.config import load_project_config, save_config
from devsynth.domain.models.requirement import RequirementPriority, RequirementType
from devsynth.interface.progress_utils import run_with_progress
from devsynth.interface.ux_bridge import sanitize_output
from devsynth.interface.webui.commands import (
    CommandHandlingMixin,
    SetupWizard,
    cli_utils,
    inspect_code_cmd,
)
from devsynth.interface.webui_bridge import WebUIBridge
from devsynth.logging_setup import DevSynthLogger

try:
    from devsynth.core.workflows import gather_requirements
except ImportError:  # pragma: no cover - optional dependency
    gather_requirements = None


logger = DevSynthLogger(__name__)


class ProjectSetupPages(CommandHandlingMixin):
    """Pages focused on onboarding and requirements capture."""

    def onboarding_page(self) -> None:
        st = self.streamlit
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
                        cmd = self._cli("init_cmd")
                        if cmd:
                            cmd(
                                root=project_root or path,
                                language=language,
                                goals=goals or None,
                                memory_backend="kuzu",
                                bridge=self,
                            )
                        st.session_state.nav = "Requirements"
            if st.button("Guided Setup", key="guided_setup"):
                with st.spinner("Starting guided setup..."):
                    if SetupWizard is None:  # pragma: no cover - defensive fallback
                        raise RuntimeError("SetupWizard is unavailable")
                    SetupWizard(self).run()

    def requirements_page(self) -> None:
        st = self.streamlit
        st.header("Requirements Gathering")
        with st.expander("Specification Generation", expanded=True):
            with st.form("requirements"):
                req_file = st.text_input("Requirements File", "requirements.md")
                if not req_file:
                    st.error("Please enter a requirements file path")

                submitted = st.form_submit_button("Generate Specs")
                if submitted and req_file:
                    if not Path(req_file).exists():
                        st.error(f"Requirements file '{req_file}' not found")
                        st.info("Make sure the file exists and the path is correct")
                    else:
                        with st.spinner("Generating specifications..."):
                            cmd = self._cli("spec_cmd")
                            if cmd:
                                self._handle_command_errors(
                                    cmd,
                                    "Failed to generate specifications",
                                    requirements_file=req_file,
                                    bridge=self,
                                )
        if hasattr(st, "divider"):
            st.divider()
        with st.expander("Inspect Requirements", expanded=True):
            with st.form("inspect"):
                input_file = st.text_input("Inspect File", "requirements.md")
                if not input_file:
                    st.error("Please enter a file path to inspect")

                submitted = st.form_submit_button("Inspect Requirements")
                if submitted and input_file:
                    if not Path(input_file).exists():
                        st.error(f"File '{input_file}' not found")
                        st.info("Make sure the file exists and the path is correct")
                    else:
                        with st.spinner("Inspecting requirements..."):
                            cmd = self._cli("inspect_cmd")
                            if cmd:
                                self._handle_command_errors(
                                    cmd,
                                    "Failed to inspect requirements",
                                    input_file=input_file,
                                    interactive=False,
                                    bridge=self,
                                )
        if hasattr(st, "divider"):
            st.divider()
        with st.expander("Specification Editor", expanded=True):
            spec_path = st.text_input("Specification File", "specs.md")
            if not spec_path:
                st.error("Please enter a specification file path")

            if st.button("Load Spec", key="load_spec") and spec_path:
                try:
                    with open(spec_path, encoding="utf-8") as f:
                        st.session_state.spec_content = f.read()
                    st.success(f"Loaded specification from {spec_path}")
                except FileNotFoundError:
                    st.error(f"Specification file '{spec_path}' not found")
                    st.info("Creating a new specification file")
                    st.session_state.spec_content = ""
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Error loading specification: {exc}")
                    st.session_state.spec_content = ""

            content = st.text_area(
                "Specification Content",
                st.session_state.get("spec_content", ""),
                height=300,
            )

            col1, col2 = st.columns(2)
            if col1.button("Save Spec", key="save_spec") and spec_path:
                try:
                    with open(spec_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    st.success(f"Saved specification to {spec_path}")

                    with st.spinner("Regenerating specifications..."):
                        cmd = self._cli("spec_cmd")
                        if cmd:
                            self._handle_command_errors(
                                cmd,
                                "Failed to regenerate specifications",
                                requirements_file=spec_path,
                                bridge=self,
                            )
                    st.session_state.spec_content = content
                    st.markdown(content)
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Error saving specification: {exc}")

            if col2.button("Save Only", key="save_only") and spec_path:
                try:
                    with open(spec_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    st.success(f"Saved specification to {spec_path}")
                    st.session_state.spec_content = content
                    st.markdown(content)
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Error saving specification: {exc}")
        if hasattr(st, "divider"):
            st.divider()
        self._requirements_wizard()
        if hasattr(st, "divider"):
            st.divider()
        self._gather_wizard()

    def _validate_requirements_step(self, wizard_state, step: int) -> bool:
        if step == 1:
            return wizard_state.get("title", "") != ""
        if step == 2:
            return wizard_state.get("description", "") != ""
        if step == 3:
            return wizard_state.get("type", "") != ""
        if step == 4:
            return wizard_state.get("priority", "") != ""
        if step == 5:
            return True
        return True

    def _save_requirements(
        self, wizard_manager, temp_keys: Sequence[str] | None = None
    ):
        try:
            result = {
                "title": wizard_manager.get_value("title"),
                "description": wizard_manager.get_value("description"),
                "type": wizard_manager.get_value("type"),
                "priority": wizard_manager.get_value("priority"),
                "constraints": [
                    c.strip()
                    for c in wizard_manager.get_value("constraints", "").split(",")
                    if c.strip()
                ],
            }
            with open("requirements_wizard.json", "w", encoding="utf-8") as f:
                f.write(json.dumps(result, indent=2))
            self.display_result(
                "[green]Requirements saved to requirements_wizard.json[/green]",
                message_type="success",
            )
            if not wizard_manager.set_completed(True):
                logger.warning("Failed to mark requirements_wizard as completed")
            if not wizard_manager.reset_wizard_state():
                logger.warning("Failed to reset requirements_wizard wizard state")
            logger.debug("Reset requirements_wizard wizard state after completion")
            wizard_manager.clear_temporary_state(temp_keys)
            return result
        except Exception as exc:  # pragma: no cover - defensive
            self.display_result(
                f"[red]ERROR saving requirements: {exc}[/red]",
                message_type="error",
                highlight=False,
            )
            return None

    def _handle_requirements_navigation(
        self,
        wizard_manager,
        wizard_state,
        temp_keys: Sequence[str] | None = None,
    ):
        current_step = wizard_state.get_current_step()
        st = self.streamlit
        col1, col2, col3 = st.columns(3)

        if current_step > 1 and col1.button(
            "Previous", key=f"previous_button_{current_step}"
        ):
            if not wizard_manager.previous_step():
                self.display_result(
                    "Error navigating to previous step", message_type="error"
                )

        if current_step < wizard_state.get_total_steps():
            if col2.button("Next", key=f"next_button_{current_step}"):
                if self._validate_requirements_step(wizard_state, current_step):
                    if not wizard_manager.next_step():
                        self.display_result(
                            "Error navigating to next step", message_type="error"
                        )
                else:
                    self.display_result(
                        "Please fill in all required fields", message_type="error"
                    )

        if current_step == wizard_state.get_total_steps():
            if col2.button("Save Requirements", key=f"save_button_{current_step}"):
                if self._validate_requirements_step(wizard_state, current_step):
                    return self._save_requirements(wizard_manager, temp_keys)
                self.display_result(
                    "Please fill in all required fields", message_type="error"
                )

        if col3.button("Cancel", key=f"cancel_button_{current_step}"):
            if not wizard_manager.reset_wizard_state():
                logger.warning("Failed to reset requirements_wizard wizard state")
            logger.debug("Reset requirements_wizard wizard state")
            wizard_manager.clear_temporary_state(temp_keys)
            self.display_result("Requirements wizard cancelled", message_type="info")

        return None

    def _requirements_wizard(self) -> None:
        st = self.streamlit
        try:
            wizard_name = "requirements_wizard"
            steps = 5
            initial_state = {
                "title": os.environ.get("DEVSYNTH_REQ_TITLE", ""),
                "description": os.environ.get("DEVSYNTH_REQ_DESCRIPTION", ""),
                "type": os.environ.get(
                    "DEVSYNTH_REQ_TYPE", RequirementType.FUNCTIONAL.value
                ),
                "priority": os.environ.get(
                    "DEVSYNTH_REQ_PRIORITY", RequirementPriority.MEDIUM.value
                ),
                "constraints": os.environ.get("DEVSYNTH_REQ_CONSTRAINTS", ""),
                "wizard_started": True,
            }

            temp_keys = [
                "requirements_title_input",
                "requirements_description_input",
                "requirements_type_select",
                "requirements_priority_select",
                "requirements_constraints_input",
            ]

            wizard_manager = WebUIBridge.create_wizard_manager(
                st.session_state,
                wizard_name,
                steps=steps,
                initial_state=initial_state,
            )

            wizard_state = wizard_manager.get_wizard_state()

            st.header("Requirements Wizard")

            current_step = wizard_state.get_current_step()
            step_names = ["Title", "Description", "Type", "Priority", "Constraints"]

            total_steps = wizard_state.get_total_steps()
            current_label = step_names[current_step - 1]
            st.write(f"Step {current_step} of {total_steps}: {current_label}")
            st.progress(current_step / total_steps)

            try:
                if current_step == 1:
                    title = st.text_input(
                        "Requirement Title",
                        wizard_state.get("title", ""),
                        key=temp_keys[0],
                    )
                    wizard_state.set("title", title)
                elif current_step == 2:
                    description = st.text_area(
                        "Requirement Description",
                        wizard_state.get("description", ""),
                        key=temp_keys[1],
                    )
                    wizard_state.set("description", description)
                elif current_step == 3:
                    options = [t.value for t in RequirementType]
                    current_type = wizard_state.get(
                        "type", RequirementType.FUNCTIONAL.value
                    )
                    try:
                        index = options.index(current_type)
                    except ValueError:
                        index = 0
                        wizard_state.set("type", options[0])
                    selected_type = st.selectbox(
                        "Requirement Type", options, index=index, key=temp_keys[2]
                    )
                    if selected_type in options:
                        wizard_state.set("type", selected_type)
                    else:
                        logger.warning(
                            "Invalid requirement type selected: %s", selected_type
                        )
                        wizard_state.set("type", options[index])
                elif current_step == 4:
                    options = [p.value for p in RequirementPriority]
                    current_priority = wizard_state.get(
                        "priority", RequirementPriority.MEDIUM.value
                    )
                    try:
                        index = options.index(current_priority)
                    except ValueError:
                        index = 0
                        wizard_state.set("priority", options[0])
                    selected_priority = st.selectbox(
                        "Requirement Priority",
                        options,
                        index=index,
                        key=temp_keys[3],
                    )
                    if selected_priority in options:
                        wizard_state.set("priority", selected_priority)
                    else:
                        logger.warning(
                            "Invalid requirement priority selected: %s",
                            selected_priority,
                        )
                        wizard_state.set("priority", options[index])
                elif current_step == 5:
                    constraints = st.text_area(
                        "Constraints (comma separated)",
                        wizard_state.get("constraints", ""),
                        key=temp_keys[4],
                    )
                    wizard_state.set("constraints", constraints)
            except Exception as exc:  # noqa: BLE001
                logger.error("Error rendering wizard step: %s", exc)
                self.display_result(
                    f"[red]ERROR rendering wizard step: {exc}[/red]",
                    message_type="error",
                    highlight=False,
                )
            result = self._handle_requirements_navigation(
                wizard_manager, wizard_state, temp_keys
            )
            if result is not None:
                return result

        except Exception as exc:  # noqa: BLE001
            logger.error("Unexpected error in requirements wizard: %s", exc)
            self.display_result(
                f"[red]ERROR in requirements wizard: {exc}[/red]",
                message_type="error",
                highlight=False,
            )

        return

    def _render_progress_summary(
        self,
        summary: Mapping[str, Any] | None,
        *,
        container: Any | None = None,
    ) -> None:
        if not isinstance(summary, Mapping):
            return

        st = self.streamlit
        summary_container = container or st.container()

        def _as_float(value: Any | None) -> float | None:
            try:
                return float(value)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                return None

        def _progress_fraction(
            value: Any | None, total: Any | None = None
        ) -> float | None:
            numeric = _as_float(value)
            if numeric is None:
                return None
            if total is not None:
                total_numeric = _as_float(total)
                if total_numeric in (None, 0):
                    return None
                numeric /= total_numeric
            if numeric > 1.0:
                numeric /= 100.0
            return max(0.0, min(1.0, numeric))

        def _percent_label(fraction: float | None) -> str | None:
            if fraction is None:
                return None
            return f"{int(round(fraction * 100))}%"

        def _timestamp_label(raw: Any | None) -> str | None:
            numeric = _as_float(raw)
            if numeric is None:
                return None
            return time.strftime("%H:%M:%S", time.localtime(numeric))

        def _sequence(value: Any | None) -> Sequence[Any]:
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                return value
            return []

        description = sanitize_output(str(summary.get("description", "Task progress")))
        main_fraction = _progress_fraction(summary.get("progress"))
        if main_fraction is None:
            main_fraction = _progress_fraction(
                summary.get("completed"), summary.get("total")
            )
        if main_fraction is None:
            main_fraction = 0.0

        percent_text = _percent_label(main_fraction) or "0%"
        summary_container.markdown(f"**{description}** — {percent_text} complete")
        summary_container.progress(main_fraction)

        eta_parts: list[str] = []
        eta_value = summary.get("eta")
        eta_numeric = _as_float(eta_value)
        eta_str = summary.get("eta_str")
        eta_message: str | None = None
        if eta_str:
            eta_message = f"ETA {sanitize_output(str(eta_str))}"
        elif eta_numeric is not None:
            eta_label = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(eta_numeric))
            eta_message = f"ETA {eta_label}"
        if eta_message and eta_numeric is not None:
            delta_seconds = max(0.0, eta_numeric - time.time())
            eta_message = f"{eta_message} (in {int(round(delta_seconds))}s)"
        if eta_message:
            eta_parts.append(eta_message)

        remaining_str = summary.get("remaining_str")
        if remaining_str:
            eta_parts.append(f"Remaining {sanitize_output(str(remaining_str))}")
        else:
            remaining_numeric = _as_float(summary.get("remaining"))
            if remaining_numeric is not None:
                remaining_seconds = max(0.0, remaining_numeric)
                eta_parts.append(f"Remaining {int(round(remaining_seconds))}s")

        elapsed_str = summary.get("elapsed_str")
        if elapsed_str:
            eta_parts.append(f"Elapsed {sanitize_output(str(elapsed_str))}")
        else:
            elapsed_numeric = _as_float(summary.get("elapsed"))
            if elapsed_numeric is not None:
                elapsed_seconds = max(0.0, elapsed_numeric)
                eta_parts.append(f"Elapsed {int(round(elapsed_seconds))}s")

        if eta_parts:
            summary_container.info(" • ".join(eta_parts))

        total_hint = summary.get("total")
        history = _sequence(summary.get("history"))
        if history:
            history_container = st.container()
            history_container.markdown("**History**")
            for entry in history:
                if not isinstance(entry, Mapping):
                    continue
                status = sanitize_output(str(entry.get("status", "")))
                fraction = _progress_fraction(entry.get("progress"))
                if fraction is None:
                    fraction = _progress_fraction(entry.get("completed"), total_hint)
                percent_label = _percent_label(fraction)
                timestamp_label = _timestamp_label(entry.get("time"))
                parts: list[str] = []
                if percent_label:
                    parts.append(percent_label)
                if status:
                    parts.append(status)
                if timestamp_label:
                    parts.append(timestamp_label)
                if parts:
                    history_container.markdown("- " + " • ".join(parts))

        checkpoints = _sequence(summary.get("checkpoints"))
        if checkpoints:
            checkpoint_container = st.container()
            checkpoint_container.markdown("**Checkpoints**")
            now = time.time()
            for checkpoint in checkpoints:
                if not isinstance(checkpoint, Mapping):
                    continue
                fraction = _progress_fraction(checkpoint.get("progress"))
                if fraction is None:
                    fraction = _progress_fraction(
                        checkpoint.get("completed"),
                        checkpoint.get("total") or total_hint,
                    )
                percent_label = _percent_label(fraction)
                if percent_label is None:
                    continue
                parts = [percent_label]
                checkpoint_time = _timestamp_label(checkpoint.get("time"))
                if checkpoint_time:
                    parts.append(checkpoint_time)
                cp_eta = checkpoint.get("eta")
                cp_eta_str = checkpoint.get("eta_str")
                if cp_eta_str:
                    parts.append(f"ETA {sanitize_output(str(cp_eta_str))}")
                else:
                    cp_eta_numeric = _as_float(cp_eta)
                    if cp_eta_numeric is not None:
                        cp_eta_label = time.strftime(
                            "%H:%M:%S", time.localtime(cp_eta_numeric)
                        )
                        delta = max(0.0, cp_eta_numeric - now)
                        parts.append(f"ETA {cp_eta_label} (in {int(round(delta))}s)")
                checkpoint_container.info(" • ".join(parts))

        subtask_candidates: Sequence[Any] = []
        for key in (
            "subtasks_detail",
            "subtask_details",
            "subtask_summaries",
            "subtasks",
        ):
            value = summary.get(key)
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                subtask_candidates = value
                break

        for subtask in subtask_candidates:
            if not isinstance(subtask, Mapping):
                continue
            sub_container = st.container()
            sub_description = sanitize_output(
                str(subtask.get("description", "Subtask"))
            )
            sub_fraction = _progress_fraction(subtask.get("progress"))
            if sub_fraction is None:
                sub_fraction = _progress_fraction(
                    subtask.get("completed"), subtask.get("total") or total_hint
                )
            if sub_fraction is None:
                sub_fraction = 0.0
            sub_percent = _percent_label(sub_fraction) or "0%"
            sub_container.markdown(f"**{sub_description}** — {sub_percent} complete")
            sub_container.progress(sub_fraction)

            status_text = subtask.get("status")
            if status_text:
                sub_container.markdown(f"- Status: {sanitize_output(str(status_text))}")

            sub_history = _sequence(subtask.get("history"))
            if sub_history:
                for event in sub_history:
                    if not isinstance(event, Mapping):
                        continue
                    event_status = sanitize_output(str(event.get("status", "")))
                    event_fraction = _progress_fraction(event.get("progress"))
                    if event_fraction is None:
                        event_fraction = _progress_fraction(
                            event.get("completed"), subtask.get("total") or total_hint
                        )
                    event_percent = _percent_label(event_fraction)
                    event_time = _timestamp_label(event.get("time"))
                    pieces: list[str] = []
                    if event_percent:
                        pieces.append(event_percent)
                    if event_status:
                        pieces.append(event_status)
                    if event_time:
                        pieces.append(event_time)
                    if pieces:
                        sub_container.markdown("- " + " • ".join(pieces))

            sub_checkpoints = _sequence(subtask.get("checkpoints"))
            if sub_checkpoints:
                for cp in sub_checkpoints:
                    if not isinstance(cp, Mapping):
                        continue
                    cp_fraction = _progress_fraction(cp.get("progress"))
                    if cp_fraction is None:
                        cp_fraction = _progress_fraction(
                            cp.get("completed"), subtask.get("total") or total_hint
                        )
                    cp_percent = _percent_label(cp_fraction)
                    if cp_percent is None:
                        continue
                    cp_parts = [cp_percent]
                    cp_time = _timestamp_label(cp.get("time"))
                    if cp_time:
                        cp_parts.append(cp_time)
                    cp_eta = cp.get("eta")
                    cp_eta_str = cp.get("eta_str")
                    if cp_eta_str:
                        cp_parts.append(f"ETA {sanitize_output(str(cp_eta_str))}")
                    else:
                        cp_eta_numeric = _as_float(cp_eta)
                        if cp_eta_numeric is not None:
                            cp_eta_label = time.strftime(
                                "%H:%M:%S", time.localtime(cp_eta_numeric)
                            )
                            delta = max(0.0, cp_eta_numeric - time.time())
                            cp_parts.append(
                                f"ETA {cp_eta_label} (in {int(round(delta))}s)"
                            )
                    sub_container.info(" • ".join(cp_parts))

    def _gather_wizard(self) -> None:
        st = self.streamlit
        try:
            wizard_name = "gather_wizard"
            steps = 3
            initial_state = {
                "resource_type": "",
                "resource_location": "",
                "resource_metadata": {},
                "wizard_started": False,
            }
            temp_keys = [
                "resource_type_select",
                "resource_location_input",
                "metadata_author_input",
                "metadata_version_input",
                "metadata_tags_input",
                "metadata_doc_type_select",
                "metadata_language_select",
                "metadata_custom_field_name_input",
                "metadata_custom_field_value_input",
            ]

            wizard_manager = WebUIBridge.create_wizard_manager(
                st.session_state,
                wizard_name,
                steps=steps,
                initial_state=initial_state,
            )
            wizard_state = wizard_manager.get_wizard_state()

            start_button_clicked = False
            try:
                start_button_clicked = st.button(
                    "Start Resource Gathering Wizard",
                    key="start_gather_wizard_button",
                )
            except Exception as exc:  # noqa: BLE001
                self.display_result(
                    f"[yellow]Warning: Error rendering button: {exc}[/yellow]",
                    highlight=False,
                )
                return

            if (
                not start_button_clicked
                and wizard_state.get_current_step() == 1
                and not wizard_manager.get_value("wizard_started", False)
            ):
                return

            if start_button_clicked:
                wizard_manager.reset_wizard_state()
                wizard_manager.clear_temporary_state(temp_keys)
                wizard_manager.set_value("wizard_started", True)

            st.header("Resource Gathering Wizard")

            current_step = wizard_state.get_current_step()
            gather_label = self._get_gather_step_title(current_step)
            st.write(f"Step {current_step} of {steps}: {gather_label}")
            st.progress(current_step / steps)

            if current_step == 1:
                self._handle_gather_step_1(wizard_state)
            elif current_step == 2:
                self._handle_gather_step_2(wizard_state)
            elif current_step == 3:
                self._handle_gather_step_3(wizard_state)

            col1, col2, col3 = st.columns(3)
            with col1:
                if current_step > 1 and st.button("Previous", key="previous_button"):
                    wizard_manager.previous_step()
                    st.experimental_rerun()

            with col2:
                if st.button("Cancel", key="cancel_button"):
                    wizard_manager.reset_wizard_state()
                    wizard_manager.clear_temporary_state(temp_keys)
                    self.display_result(
                        "[blue]Resource gathering canceled.[/blue]",
                        highlight=False,
                        message_type="info",
                    )
                    st.experimental_rerun()

            with col3:
                if current_step < steps:
                    if st.button("Next", key="next_button"):
                        if self._validate_gather_step(wizard_state, current_step):
                            wizard_manager.next_step()
                            st.experimental_rerun()
                else:
                    if st.button("Finish", key="finish_button"):
                        if self._validate_gather_step(wizard_state, current_step):
                            wizard_manager.set_completed(True)
                            try:
                                if gather_requirements is None:
                                    raise ImportError(
                                        "gather_requirements function not available"
                                    )
                                subtasks_meta = [
                                    {
                                        "name": self._get_gather_step_title(step_index),
                                        "total": 100,
                                    }
                                    for step_index in range(1, steps + 1)
                                ]

                                summary = run_with_progress(
                                    "Processing resources...",
                                    lambda: gather_requirements(self),
                                    self,
                                    subtasks=subtasks_meta,
                                )
                                if isinstance(summary, Mapping):
                                    self._render_progress_summary(summary)
                                self.display_result(
                                    "[green]Resources gathered successfully![/green]",
                                    highlight=False,
                                    message_type="success",
                                )
                                wizard_manager.reset_wizard_state()
                                wizard_manager.clear_temporary_state(temp_keys)
                                st.experimental_rerun()
                            except ImportError as exc:
                                self.display_result(
                                    "[red]ERROR importing gather_requirements: "
                                    f"{exc}[/red]",
                                    highlight=False,
                                    message_type="error",
                                )
                                wizard_manager.set_completed(False)
                            except Exception as exc:  # noqa: BLE001
                                self.display_result(
                                    f"[red]ERROR processing resources: {exc}[/red]",
                                    highlight=False,
                                    message_type="error",
                                )
                                wizard_manager.set_completed(False)
        except Exception as exc:  # noqa: BLE001
            self.display_result(
                f"[red]ERROR in gather wizard: {exc}[/red]",
                highlight=False,
            )

    def _get_gather_step_title(self, step: int) -> str:
        titles = {1: "Resource Type", 2: "Resource Location", 3: "Resource Metadata"}
        return titles.get(step, f"Step {step}")

    def _handle_gather_step_1(self, wizard_state):
        st = self.streamlit
        current_value = wizard_state.get("resource_type", "")

        resource_type = st.selectbox(
            "Select the type of resource to gather:",
            ["", "documentation", "code", "data", "custom"],
            index=(
                0
                if not current_value
                else ["", "documentation", "code", "data", "custom"].index(
                    current_value
                )
            ),
            key="resource_type_select",
        )

        wizard_state.set("resource_type", resource_type)

    def _handle_gather_step_2(self, wizard_state):
        st = self.streamlit
        current_value = wizard_state.get("resource_location", "")

        resource_location = st.text_input(
            "Enter the location of the resource:",
            value=current_value,
            key="resource_location_input",
        )

        wizard_state.set("resource_location", resource_location)

    def _handle_gather_step_3(self, wizard_state):
        st = self.streamlit
        metadata = wizard_state.get("resource_metadata", {})

        st.subheader("Resource Metadata")

        author = st.text_input(
            "Author:", value=metadata.get("author", ""), key="metadata_author_input"
        )

        version = st.text_input(
            "Version:", value=metadata.get("version", ""), key="metadata_version_input"
        )

        tags_str = ",".join(metadata.get("tags", []))
        tags_input = st.text_input(
            "Tags (comma-separated):", value=tags_str, key="metadata_tags_input"
        )
        tags = [tag.strip() for tag in tags_input.split(",")] if tags_input else []

        resource_type = wizard_state.get("resource_type", "")
        if resource_type == "documentation":
            doc_type = st.selectbox(
                "Documentation Type:",
                ["", "user guide", "api reference", "tutorial", "other"],
                index=(
                    0
                    if not metadata.get("doc_type")
                    else ["", "user guide", "api reference", "tutorial", "other"].index(
                        metadata.get("doc_type", "")
                    )
                ),
                key="metadata_doc_type_select",
            )
            metadata["doc_type"] = doc_type
        elif resource_type == "code":
            language = st.selectbox(
                "Programming Language:",
                ["", "python", "javascript", "go", "rust", "other"],
                index=(
                    0
                    if not metadata.get("language")
                    else ["", "python", "javascript", "go", "rust", "other"].index(
                        metadata.get("language", "")
                    )
                ),
                key="metadata_language_select",
            )
            metadata["language"] = language
        elif resource_type == "custom":
            custom_field = st.text_input(
                "Custom Field Name:",
                value=metadata.get("custom_field_name", ""),
                key="metadata_custom_field_name_input",
            )
            custom_value = st.text_input(
                "Custom Field Value:",
                value=metadata.get("custom_field_value", ""),
                key="metadata_custom_field_value_input",
            )
            if custom_field and custom_value:
                metadata[custom_field] = custom_value

        metadata.update({"author": author, "version": version, "tags": tags})

        wizard_state.set("resource_metadata", metadata)

    def _validate_gather_step(self, wizard_state, step: int) -> bool:
        if step == 1:
            resource_type = wizard_state.get("resource_type", "")
            if not resource_type:
                self.display_result(
                    "[red]Error: Please select a resource type.[/red]",
                    highlight=False,
                    message_type="error",
                )
                return False
        elif step == 2:
            resource_location = wizard_state.get("resource_location", "")
            if not resource_location:
                self.display_result(
                    "[red]Error: Please enter a resource location.[/red]",
                    highlight=False,
                    message_type="error",
                )
                return False
        elif step == 3:
            metadata = wizard_state.get("resource_metadata", {})
            if not metadata.get("author"):
                self.display_result(
                    "[red]Error: Please enter an author.[/red]",
                    highlight=False,
                    message_type="error",
                )
                return False
            if not metadata.get("version"):
                self.display_result(
                    "[red]Error: Please enter a version.[/red]",
                    highlight=False,
                    message_type="error",
                )
                return False

        return True


class LifecyclePages(CommandHandlingMixin):
    """Pages that drive analysis, synthesis, and alignment workflows."""

    def analysis_page(self) -> None:
        st = self.streamlit
        st.header("Code Analysis")

        def get_session_value(key, default=None):
            return WebUIBridge.get_session_value(st.session_state, key, default)

        def set_session_value(key, value):
            WebUIBridge.set_session_value(st.session_state, key, value)

        saved_path = get_session_value("analysis_path", ".")

        with st.expander("Inspect Code", expanded=True):
            with st.form("analysis"):
                path = st.text_input("Path", saved_path)
                if not path:
                    st.error("Please enter a path to inspect")

                submitted = st.form_submit_button("Inspect")
                if submitted and path:
                    set_session_value("analysis_path", path)

                    if not Path(path).exists():
                        st.error(f"Path '{path}' not found")
                        st.info(
                            "Make sure the directory or file exists "
                            "and the path is correct"
                        )
                    else:
                        with st.spinner("Inspecting code..."):
                            cmd = inspect_code_cmd
                            if cmd:
                                self._handle_command_errors(
                                    cmd,
                                    "Failed to inspect code",
                                    path=path,
                                    bridge=self,
                                )

    def synthesis_page(self) -> None:
        st = self.streamlit
        st.header("Synthesis Execution")

        def get_session_value(key, default=None):
            return WebUIBridge.get_session_value(st.session_state, key, default)

        def set_session_value(key, value):
            WebUIBridge.set_session_value(st.session_state, key, value)

        saved_spec_file = get_session_value("synthesis_spec_file", "specs.md")

        with st.expander("Generate Tests", expanded=True):
            with st.form("tests"):
                spec_file = st.text_input("Spec File", saved_spec_file)
                if not spec_file:
                    st.error("Please enter a specification file path")

                submitted = st.form_submit_button("Generate Tests")
                if submitted and spec_file:
                    set_session_value("synthesis_spec_file", spec_file)

                    if not Path(spec_file).exists():
                        st.error(f"Specification file '{spec_file}' not found")
                        st.info("Make sure the file exists and the path is correct")
                    else:
                        with st.spinner("Generating tests..."):
                            cmd = self._cli("test_cmd")
                            if cmd:
                                self._handle_command_errors(
                                    cmd,
                                    "Failed to generate tests",
                                    spec_file=spec_file,
                                    bridge=self,
                                )

        if hasattr(st, "divider"):
            st.divider()
        with st.expander("Execute Code Generation", expanded=True):
            if st.button("Generate Code"):
                with st.spinner("Generating code..."):
                    cmd = self._cli("code_cmd")
                    if cmd:
                        self._handle_command_errors(
                            cmd,
                            "Failed to generate code",
                            bridge=self,
                        )

            if st.button("Run Pipeline"):
                with st.spinner("Running pipeline..."):
                    cmd = self._cli("run_pipeline_cmd")
                    if cmd:
                        self._handle_command_errors(
                            cmd,
                            "Failed to run pipeline",
                            bridge=self,
                        )

    def edrr_cycle_page(self) -> None:
        st = self.streamlit
        st.header("EDRR Cycle")
        with st.form("edrr"):
            manifest = st.text_input("Manifest Path", "manifest.yaml")
            auto = st.checkbox("Auto Mode", value=False)
            submitted = st.form_submit_button("Run EDRR Cycle")
        if submitted:
            if not manifest:
                st.error("Please provide a manifest path")
            elif not Path(manifest).exists():
                st.error(f"Manifest file '{manifest}' not found")
                with st.expander("How to create a manifest file"):
                    st.markdown(
                        """
                    A manifest file is a YAML file that defines the structure of
                    your project. It includes information about requirements,
                    specifications, and code organization.

                    Example manifest.yaml:
                    ```yaml
                    project:
                      name: my-project
                      description: A sample project
                    requirements:
                      path: requirements.md
                    specifications:
                      path: specs.md
                    ```
                    """
                    )
            else:
                with st.spinner("Running EDRR cycle..."):
                    import sys

                    module = sys.modules.get(
                        "devsynth.application.cli.commands.edrr_cycle_cmd"
                    )
                    if module is None:  # pragma: no cover - defensive fallback
                        module = importlib.import_module(
                            "devsynth.application.cli.commands.edrr_cycle_cmd"
                        )

                    original = module.bridge
                    module.bridge = self
                    try:
                        self._handle_command_errors(
                            module.edrr_cycle_cmd,
                            "Failed to run EDRR cycle",
                            manifest=manifest,
                            auto=auto,
                        )
                    finally:
                        module.bridge = original

    def alignment_page(self) -> None:
        st = self.streamlit
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
                    module = importlib.import_module(
                        "devsynth.application.cli.commands.align_cmd"
                    )

                original = module.bridge
                module.bridge = self
                try:
                    module.align_cmd(path=path, verbose=verbose)
                finally:
                    module.bridge = original

    def alignment_metrics_page(self) -> None:
        st = self.streamlit
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
                    module = importlib.import_module(
                        "devsynth.application.cli.commands.alignment_metrics_cmd"
                    )

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


class OperationsPages(CommandHandlingMixin):
    """Configuration and generation pages exposed by the WebUI."""

    def config_page(self) -> None:
        st = self.streamlit
        st.header("Configuration Editing")

        def get_session_value(key, default=None):
            return WebUIBridge.get_session_value(st.session_state, key, default)

        def set_session_value(key, value):
            WebUIBridge.set_session_value(st.session_state, key, value)

        try:
            cfg = load_project_config()

            saved_offline_mode = get_session_value(
                "config_offline_mode", cfg.config.offline_mode
            )

            offline_toggle = st.toggle("Offline Mode", value=saved_offline_mode)

            if saved_offline_mode != offline_toggle:
                set_session_value("config_offline_mode", offline_toggle)

            if st.button("Save Offline Mode"):
                cfg.config.offline_mode = offline_toggle
                with st.spinner("Saving configuration..."):
                    try:
                        save_config(
                            cfg.config,
                            use_pyproject=cfg.use_pyproject,
                            path=cfg.config.project_root,
                        )
                        st.success("Offline mode setting saved successfully")
                    except Exception as exc:  # noqa: BLE001
                        st.error(f"Error saving configuration: {exc}")
                        st.info(
                            "Make sure you have write permissions to the "
                            "configuration file"
                        )

            with st.expander("Update Settings", expanded=True):
                with st.form("config"):
                    key = st.text_input("Key")
                    value = st.text_input("Value")

                    if not key and st.form_submit_button():
                        st.error("Please enter a configuration key")

                    submitted = st.form_submit_button("Update")
                    if submitted and key:
                        with st.spinner("Updating configuration..."):
                            cmd = self._cli("config_cmd")
                            if cmd:
                                self._handle_command_errors(
                                    cmd,
                                    "Failed to update configuration",
                                    key=key,
                                    value=value,
                                    bridge=self,
                                )
        except Exception as exc:  # noqa: BLE001
            st.error(f"Error loading configuration: {exc}")

    def inspect_config_page(self) -> None:
        st = self.streamlit
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
                    module = importlib.import_module(
                        "devsynth.application.cli.commands.inspect_config_cmd"
                    )

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
        st = self.streamlit
        st.header("Validate Manifest")
        with st.form("validate_manifest"):
            manifest = st.text_input("Manifest Path", "manifest.yaml")
            schema = st.text_input("Schema Path", "")
            submitted = st.form_submit_button("Validate Manifest")
        if submitted:
            with st.spinner("Validating manifest..."):
                import sys

                module = sys.modules.get(
                    "devsynth.application.cli.commands." "validate_manifest_cmd"
                )
                if module is None:  # pragma: no cover - defensive fallback
                    module = importlib.import_module(
                        "devsynth.application.cli.commands.validate_manifest_cmd"
                    )

                original = module.bridge
                module.bridge = self
                try:
                    module.validate_manifest_cmd(
                        manifest=manifest,
                        schema=schema or None,
                    )
                finally:
                    module.bridge = original

    def validate_metadata_page(self) -> None:
        st = self.streamlit
        st.header("Validate Metadata")
        with st.form("validate_metadata"):
            path = st.text_input("Metadata Path", "docs/")
            fail_fast = self.confirm_choice("Fail Fast", default=True)
            submitted = st.form_submit_button("Validate Metadata")
        if submitted:
            with st.spinner("Validating metadata..."):
                import sys

                module = sys.modules.get(
                    "devsynth.application.cli.commands." "validate_metadata_cmd"
                )
                if module is None:  # pragma: no cover - defensive fallback
                    module = importlib.import_module(
                        "devsynth.application.cli.commands.validate_metadata_cmd"
                    )

                original = module.bridge
                module.bridge = self
                try:
                    module.validate_metadata_cmd(
                        path=path,
                        fail_fast=fail_fast,
                    )
                finally:
                    module.bridge = original

    def test_metrics_page(self) -> None:
        st = self.streamlit
        st.header("Test Metrics")
        with st.form("test_metrics"):
            repo_path = st.text_input("Repository Path", ".")
            days = st.text_input("Lookback Days", "30")
            output_file = st.text_input("Output File", "")
            submitted = st.form_submit_button("Collect Metrics")
        if submitted:
            with st.spinner("Collecting test metrics..."):
                import sys

                module = sys.modules.get(
                    "devsynth.application.cli.commands." "test_metrics_cmd"
                )
                if module is None:  # pragma: no cover - defensive fallback
                    module = importlib.import_module(
                        "devsynth.application.cli.commands.test_metrics_cmd"
                    )

                original = module.bridge
                module.bridge = self
                try:
                    module.test_metrics_cmd(
                        repo_path=repo_path,
                        days=int(days),
                        output_file=output_file or None,
                    )
                finally:
                    module.bridge = original

    def docs_generation_page(self) -> None:
        st = self.streamlit
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
        st = self.streamlit
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
        st = self.streamlit
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

    def refactor_page(self) -> None:
        st = self.streamlit
        st.header("Refactor Suggestions")
        with st.form("refactor"):
            path = st.text_input("Project Path", ".")
            submitted = st.form_submit_button("Run Refactor")
        if submitted:
            with st.spinner("Running refactor analysis..."):
                cmd = self._cli("refactor_cmd")
                if cmd and cli_utils is not None:
                    original = cli_utils.bridge
                    cli_utils.bridge = self
                    try:
                        cmd(path=path or None, bridge=self)
                    finally:
                        cli_utils.bridge = original

    def webapp_page(self) -> None:
        st = self.streamlit
        st.header("Web App Helper")
        with st.form("webapp"):
            framework = st.text_input("Framework", "flask")
            name = st.text_input("Name", "webapp")
            path = st.text_input("Path", ".")
            submitted = st.form_submit_button("Generate Web App")
        if submitted:
            with st.spinner("Generating web app..."):
                cmd = self._cli("webapp_cmd")
                if cmd and cli_utils is not None:
                    original = cli_utils.bridge
                    cli_utils.bridge = self
                    try:
                        cmd(
                            framework=framework,
                            name=name,
                            path=path,
                            bridge=self,
                        )
                    finally:
                        cli_utils.bridge = original

    def serve_page(self) -> None:
        st = self.streamlit
        st.header("Serve API")
        with st.form("serve"):
            host = st.text_input(
                "Host", "0.0.0.0"
            )  # nosec B104: intentionally exposed for remote access
            port = st.number_input("Port", value=8000)
            submitted = st.form_submit_button("Start Server")
        if submitted:
            with st.spinner("Starting server..."):
                cmd = self._cli("serve_cmd")
                if cmd and cli_utils is not None:
                    original = cli_utils.bridge
                    cli_utils.bridge = self
                    try:
                        cmd(host=host, port=int(port), bridge=self)
                    finally:
                        cli_utils.bridge = original

    def dbschema_page(self) -> None:
        st = self.streamlit
        st.header("Database Schema")
        with st.form("dbschema"):
            db_type = st.text_input("Database Type", "sqlite")
            name = st.text_input("Name", "database")
            path = st.text_input("Path", ".")
            submitted = st.form_submit_button("Generate Schema")
        if submitted:
            with st.spinner("Generating schema..."):
                cmd = self._cli("dbschema_cmd")
                if cmd and cli_utils is not None:
                    original = cli_utils.bridge
                    cli_utils.bridge = self
                    try:
                        cmd(
                            db_type=db_type,
                            name=name,
                            path=path,
                            bridge=self,
                        )
                    finally:
                        cli_utils.bridge = original


class SupportPages(CommandHandlingMixin):
    """Health-check pages used for diagnostics."""

    def doctor_page(self) -> None:
        st = self.streamlit
        st.header("Doctor")
        with st.spinner("Validating configuration..."):
            import sys

            doc_module = sys.modules.get("devsynth.application.cli.commands.doctor_cmd")
            if doc_module is None:  # pragma: no cover - defensive fallback
                import devsynth.application.cli.commands.doctor_cmd as doc_module

            original = doc_module.bridge
            doc_module.bridge = self
            try:
                doc_module.doctor_cmd()
            finally:
                doc_module.bridge = original

    def diagnostics_page(self) -> None:
        st = self.streamlit
        st.header("Diagnostics")
        audit_log = Path("dialectical_audit.log")
        with st.expander("Dialectical Audit Log"):
            if audit_log.exists():
                st.code(audit_log.read_text())
            else:
                st.write("No audit logs available.")
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


class PageRenderer(
    ProjectSetupPages,
    LifecyclePages,
    OperationsPages,
    SupportPages,
):
    """Aggregate mixin exposing all WebUI pages and navigation helpers."""

    def navigation_items(self) -> dict[str, Callable[[], None]]:
        return {
            "Onboarding": self.onboarding_page,
            "Requirements": self.requirements_page,
            "Analysis": self.analysis_page,
            "Synthesis": self.synthesis_page,
            "EDRR Cycle": self.edrr_cycle_page,
            "Alignment": self.alignment_page,
            "Alignment Metrics": self.alignment_metrics_page,
            "Inspect Config": self.inspect_config_page,
            "Validate Manifest": self.validate_manifest_page,
            "Validate Metadata": self.validate_metadata_page,
            "Test Metrics": self.test_metrics_page,
            "Generate Docs": self.docs_generation_page,
            "Ingest": self.ingestion_page,
            "API Spec": self.apispec_page,
            "Refactor": self.refactor_page,
            "Web App": self.webapp_page,
            "Serve": self.serve_page,
            "DB Schema": self.dbschema_page,
            "Config": self.config_page,
            "Doctor": self.doctor_page,
            "Diagnostics": self.diagnostics_page,
        }


__all__ = [
    "PageRenderer",
    "ProjectSetupPages",
    "LifecyclePages",
    "OperationsPages",
    "SupportPages",
]
