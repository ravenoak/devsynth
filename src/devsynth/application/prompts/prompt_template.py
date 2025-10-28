"""
Prompt Template module.

This module defines the PromptTemplate and PromptTemplateVersion classes for
managing prompt templates with versioning support.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class PromptTemplateVersion:
    """
    Represents a specific version of a prompt template.

    Attributes:
        version_id: Unique identifier for this version
        template_text: The actual template text with placeholders
        created_at: When this version was created
        metadata: Additional metadata for this version
    """

    template_text: str
    version_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def render(self, variables: dict[str, str]) -> str:
        """
        Render the template with the provided variables.

        Args:
            variables: Dictionary of variable names and their values

        Returns:
            The rendered prompt with variables substituted
        """
        rendered_text = self.template_text

        # Replace each variable in the template
        for var_name, var_value in variables.items():
            placeholder = f"{{{var_name}}}"
            rendered_text = rendered_text.replace(placeholder, var_value)

        return rendered_text


@dataclass
class PromptTemplate:
    """
    Represents a prompt template with version history.

    Attributes:
        name: Unique name for this template
        description: Description of the template's purpose
        versions: List of versions, ordered by creation time (newest last)
        metadata: Additional metadata for this template
        edrr_phase: The EDRR phase this template is associated with (if any)
    """

    name: str
    description: str
    versions: list[PromptTemplateVersion] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    edrr_phase: str | None = None

    def add_version(
        self, template_text: str, metadata: dict[str, Any] | None = None
    ) -> PromptTemplateVersion:
        """
        Add a new version of this template.

        Args:
            template_text: The template text with placeholders
            metadata: Optional metadata for this version

        Returns:
            The newly created version
        """
        version = PromptTemplateVersion(
            template_text=template_text, metadata=metadata or {}
        )
        self.versions.append(version)
        return version

    def get_latest_version(self) -> PromptTemplateVersion | None:
        """
        Get the latest version of this template.

        Returns:
            The latest version, or None if no versions exist
        """
        if not self.versions:
            return None
        return self.versions[-1]

    def get_version(self, version_id: str) -> PromptTemplateVersion | None:
        """
        Get a specific version of this template.

        Args:
            version_id: The ID of the version to retrieve

        Returns:
            The requested version, or None if not found
        """
        for version in self.versions:
            if version.version_id == version_id:
                return version
        return None

    def render(
        self, variables: dict[str, str], version_id: str | None = None
    ) -> str:
        """
        Render the template with the provided variables.

        Args:
            variables: Dictionary of variable names and their values
            version_id: Optional ID of the version to use (uses latest if not specified)

        Returns:
            The rendered prompt with variables substituted

        Raises:
            ValueError: If no versions exist or the specified version is not found
        """
        if version_id:
            version = self.get_version(version_id)
            if not version:
                raise ValueError(
                    f"Version {version_id} not found for template {self.name}"
                )
        else:
            version = self.get_latest_version()
            if not version:
                raise ValueError(f"No versions exist for template {self.name}")

        return version.render(variables)
