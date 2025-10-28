"""
Prompt Manager module.

This module defines the PromptManager class for managing prompt templates,
providing a centralized system for all agents to access and use templates.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from devsynth.application.prompts.auto_tuning import (
    PromptAutoTuner,
    PromptAutoTuningError,
)
from devsynth.application.prompts.prompt_efficacy import PromptEfficacyTracker
from devsynth.application.prompts.prompt_reflection import PromptReflection
from devsynth.application.prompts.prompt_template import (
    PromptTemplate,
    PromptTemplateVersion,
)
from devsynth.logging_setup import DevSynthLogger

# Create a logger for this module
logger = DevSynthLogger(__name__)

# Load default configuration for feature flags
_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[3] / "config" / "default.yml"
try:
    with open(_DEFAULT_CONFIG_PATH) as f:
        _DEFAULT_CONFIG = yaml.safe_load(f) or {}
except Exception:
    _DEFAULT_CONFIG = {}


class PromptManager:
    """
    Manages prompt templates for all agents in the system.

    This class provides methods for registering, retrieving, and rendering
    prompt templates, as well as tracking their usage and efficacy.
    """

    def __init__(
        self,
        storage_path: str | None = None,
        efficacy_tracker: PromptEfficacyTracker | None = None,
        reflection_system: PromptReflection | None = None,
        config: dict[str, Any] | None = None,
    ):
        """
        Initialize the prompt manager.

        Args:
            storage_path: Path to store prompt templates (defaults to .devsynth/prompts)
            efficacy_tracker: Optional efficacy tracker to use
            reflection_system: Optional reflection system to use
        """
        self.templates: dict[str, PromptTemplate] = {}
        self.storage_path = storage_path or os.path.join(
            os.getcwd(), ".devsynth", "prompts"
        )
        self.efficacy_tracker = efficacy_tracker
        self.reflection_system = reflection_system
        self.config = config or _DEFAULT_CONFIG
        feature_cfg = self.config.get("features", {})
        self.auto_tuning_enabled = feature_cfg.get("prompt_auto_tuning", False)
        self.auto_tuner: PromptAutoTuner | None = None
        self._last_variant_ids: dict[str, str] = {}

        if self.auto_tuning_enabled:
            self.auto_tuner = PromptAutoTuner(storage_path=self.storage_path)
            logger.info("Prompt auto-tuning enabled")

        # Create the storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)

        # Load any existing templates
        self._load_templates()

        logger.info(
            f"Prompt manager initialized with storage path: {self.storage_path}"
        )

    def register_template(
        self,
        name: str,
        description: str,
        template_text: str,
        metadata: dict[str, Any] | None = None,
        edrr_phase: str | None = None,
    ) -> PromptTemplate:
        """
        Register a new prompt template.

        Args:
            name: Unique name for the template
            description: Description of the template's purpose
            template_text: The template text with placeholders
            metadata: Optional metadata for the template
            edrr_phase: Optional EDRR phase this template is associated with

        Returns:
            The newly created template

        Raises:
            ValueError: If a template with the given name already exists
        """
        if name in self.templates:
            raise ValueError(f"Template with name '{name}' already exists")

        template = PromptTemplate(
            name=name,
            description=description,
            metadata=metadata or {},
            edrr_phase=edrr_phase,
        )

        # Add the initial version
        template.add_version(template_text, metadata)

        # Store the template
        self.templates[name] = template
        self._save_template(template)

        if self.auto_tuner:
            self.auto_tuner.register_template(name, template_text)

        logger.info(f"Registered new prompt template: {name}")
        return template

    def get_template(self, name: str) -> PromptTemplate | None:
        """
        Get a prompt template by name.

        Args:
            name: The name of the template to retrieve

        Returns:
            The template, or None if not found
        """
        return self.templates.get(name)

    def update_template(
        self, name: str, template_text: str, metadata: dict[str, Any] | None = None
    ) -> PromptTemplateVersion | None:
        """
        Update a prompt template by adding a new version.

        Args:
            name: The name of the template to update
            template_text: The new template text
            metadata: Optional metadata for the new version

        Returns:
            The newly created version, or None if the template doesn't exist
        """
        template = self.get_template(name)
        if not template:
            logger.warning(f"Cannot update non-existent template: {name}")
            return None

        version = template.add_version(template_text, metadata)
        self._save_template(template)

        if self.auto_tuner:
            self.auto_tuner.register_template(name, template_text)

        logger.info(f"Updated template '{name}' with new version {version.version_id}")
        return version

    def render_prompt(
        self, name: str, variables: dict[str, str], version_id: str | None = None
    ) -> str | None:
        """
        Render a prompt template with the provided variables.

        Args:
            name: The name of the template to render
            variables: Dictionary of variable names and their values
            version_id: Optional ID of the version to use (uses latest if not specified)

        Returns:
            The rendered prompt, or None if the template doesn't exist
        """
        template = self.get_template(name)
        if not template:
            logger.warning(f"Cannot render non-existent template: {name}")
            return None

        try:
            if self.auto_tuner and name in self.auto_tuner.prompt_variants:
                variant = self.auto_tuner.select_variant(name)
                self._last_variant_ids[name] = variant.variant_id
                rendered = variant.template
                for var_name, var_value in variables.items():
                    rendered = rendered.replace(f"{{{var_name}}}", var_value)
                if self.efficacy_tracker:
                    self.efficacy_tracker.track_usage(name, variant.variant_id)
                return rendered

            rendered = template.render(variables, version_id)

            # Track usage if efficacy tracker is available
            if self.efficacy_tracker:
                self.efficacy_tracker.track_usage(
                    name, version_id or template.get_latest_version().version_id
                )

            return rendered
        except (ValueError, PromptAutoTuningError) as e:
            logger.error(f"Error rendering template '{name}': {str(e)}")
            return None

    def render_and_reflect(
        self, name: str, variables: dict[str, str], version_id: str | None = None
    ) -> dict[str, Any]:
        """
        Render a prompt template and set up reflection for the response.

        Args:
            name: The name of the template to render
            variables: Dictionary of variable names and their values
            version_id: Optional ID of the version to use

        Returns:
            A dictionary containing the rendered prompt and a reflection ID
        """
        rendered = self.render_prompt(name, variables, version_id)
        if not rendered or not self.reflection_system:
            return {"prompt": rendered, "reflection_id": None}

        reflection_id = self.reflection_system.prepare_reflection(
            name, variables, rendered
        )
        return {"prompt": rendered, "reflection_id": reflection_id}

    def process_response(self, reflection_id: str, response: str) -> dict[str, Any]:
        """
        Process a response to a prompt, triggering reflection if available.

        Args:
            reflection_id: The ID of the reflection to use
            response: The response to process

        Returns:
            A dictionary containing the reflection results
        """
        if not self.reflection_system or not reflection_id:
            return {"reflection": None}

        reflection = self.reflection_system.reflect(reflection_id, response)
        return {"reflection": reflection}

    def record_tuning_feedback(
        self,
        name: str,
        success: bool | None = None,
        feedback_score: float | None = None,
    ) -> None:
        """Record feedback for the last rendered variant of a template."""
        if not self.auto_tuner:
            return

        variant_id = self._last_variant_ids.get(name)
        if not variant_id:
            logger.warning(
                f"No variant recorded for template '{name}' to provide feedback"
            )
            return

        try:
            self.auto_tuner.record_feedback(name, variant_id, success, feedback_score)
        except PromptAutoTuningError as e:
            logger.error(f"Failed to record auto-tuning feedback: {e}")

    def list_templates(self, edrr_phase: str | None = None) -> list[dict[str, Any]]:
        """
        List all available templates, optionally filtered by EDRR phase.

        Args:
            edrr_phase: Optional EDRR phase to filter by

        Returns:
            A list of template metadata dictionaries
        """
        result = []
        for name, template in self.templates.items():
            if edrr_phase and template.edrr_phase != edrr_phase:
                continue

            latest = template.get_latest_version()
            result.append(
                {
                    "name": name,
                    "description": template.description,
                    "edrr_phase": template.edrr_phase,
                    "versions": len(template.versions),
                    "latest_version_id": latest.version_id if latest else None,
                    "created_at": latest.created_at.isoformat() if latest else None,
                }
            )

        return result

    def _load_templates(self) -> None:
        """Load templates from the storage path."""
        no_file_logging = os.environ.get("DEVSYNTH_NO_FILE_LOGGING", "0").lower() in (
            "1",
            "true",
            "yes",
        )

        if no_file_logging:
            logger.debug("DEVSYNTH_NO_FILE_LOGGING set; skipping template load")
            return

        template_files = Path(self.storage_path).glob("*.json")
        for file_path in template_files:
            try:
                with open(file_path) as f:
                    data = json.load(f)

                template = self._deserialize_template(data)
                if template:
                    self.templates[template.name] = template
                    logger.debug(f"Loaded template: {template.name}")
            except Exception as e:
                logger.error(f"Error loading template from {file_path}: {str(e)}")

    def _save_template(self, template: PromptTemplate) -> None:
        """Save a template to the storage path."""
        # Skip file writes when file logging is disabled for tests
        no_file_logging = os.environ.get("DEVSYNTH_NO_FILE_LOGGING", "0").lower() in (
            "1",
            "true",
            "yes",
        )

        if no_file_logging:
            logger.debug(
                "DEVSYNTH_NO_FILE_LOGGING set; not persisting template %s to disk",
                template.name,
            )
            return

        file_path = os.path.join(self.storage_path, f"{template.name}.json")
        try:
            with open(file_path, "w") as f:
                json.dump(self._serialize_template(template), f, indent=2)
            logger.debug(f"Saved template: {template.name}")
        except Exception as e:
            logger.error(f"Error saving template {template.name}: {str(e)}")

    def _serialize_template(self, template: PromptTemplate) -> dict[str, Any]:
        """Serialize a template to a dictionary."""
        return {
            "name": template.name,
            "description": template.description,
            "metadata": template.metadata,
            "edrr_phase": template.edrr_phase,
            "versions": [
                {
                    "version_id": v.version_id,
                    "template_text": v.template_text,
                    "created_at": v.created_at.isoformat(),
                    "metadata": v.metadata,
                }
                for v in template.versions
            ],
        }

    def _deserialize_template(self, data: dict[str, Any]) -> PromptTemplate | None:
        """Deserialize a template from a dictionary."""
        try:
            template = PromptTemplate(
                name=data["name"],
                description=data["description"],
                metadata=data.get("metadata", {}),
                edrr_phase=data.get("edrr_phase"),
            )

            for v_data in data.get("versions", []):
                version = PromptTemplateVersion(
                    version_id=v_data["version_id"],
                    template_text=v_data["template_text"],
                    created_at=datetime.fromisoformat(v_data["created_at"]),
                    metadata=v_data.get("metadata", {}),
                )
                template.versions.append(version)

            return template
        except Exception as e:
            logger.error(f"Error deserializing template: {str(e)}")
            return None
