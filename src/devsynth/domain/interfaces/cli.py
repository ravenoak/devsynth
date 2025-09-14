from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class CLIInterface(ABC):
    """Interface for CLI operations."""

    @abstractmethod
    def initialize_project(self, path: str) -> None:
        """Initialize a new project at the specified path."""
        raise NotImplementedError

    @abstractmethod
    def generate_spec(self, requirements_file: str) -> None:
        """Generate specifications from requirements."""
        raise NotImplementedError

    @abstractmethod
    def generate_tests(self, spec_file: str) -> None:
        """Generate tests from specifications."""
        raise NotImplementedError

    @abstractmethod
    def generate_code(self) -> None:
        """Generate code from tests."""
        raise NotImplementedError

    @abstractmethod
    def run(self, target: str | None = None) -> None:
        """Execute the generated code or a specific target."""
        raise NotImplementedError

    @abstractmethod
    def configure(
        self, key: str | None = None, value: str | None = None
    ) -> dict[str, Any]:
        """View or set configuration options."""
        raise NotImplementedError
