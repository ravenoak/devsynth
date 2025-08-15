"""Test agent for the DevSynth system."""

from pathlib import Path
from typing import Any, Dict, List

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger
from devsynth.testing.generation import (
    scaffold_integration_tests as _scaffold_integration_tests,
)
from devsynth.testing.generation import (
    write_scaffolded_tests as _write_scaffolded_tests,
)

from .base import BaseAgent

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError

__all__ = ["TestAgent", "scaffold_integration_tests", "write_scaffolded_tests"]


def scaffold_integration_tests(test_names: List[str]) -> Dict[str, str]:
    """Public hook for generating placeholder integration test modules.

    This function re-exports :func:`devsynth.testing.generation.scaffold_integration_tests`
    so callers can generate integration test scaffolds without instantiating
    :class:`TestAgent`.
    """

    return _scaffold_integration_tests(test_names)


def write_scaffolded_tests(directory: Path, test_names: List[str]) -> Dict[Path, str]:
    """Public hook for writing placeholder integration test modules to disk."""

    return _write_scaffolded_tests(directory, test_names)


class TestAgent(BaseAgent):
    """Agent responsible for creating tests (BDD and unit tests)."""

    # Avoid pytest collecting this agent class as a test case
    __test__ = False

    def scaffold_integration_tests(
        self, test_names: List[str], output_dir: Path | None = None
    ) -> Dict[str, str]:
        """Create placeholder integration test modules and optionally write them.

        Args:
            test_names: List of base names for integration tests.
            output_dir: Directory where test scaffolds should be written. If
                ``None`` the scaffolds are only returned.

        Returns:
            Dictionary mapping filenames to placeholder test content. When
            ``output_dir`` is provided, the mapping keys are file names rather
            than full paths.
        """

        names = test_names or ["placeholder"]
        if output_dir is not None:
            written = write_scaffolded_tests(output_dir, names)
            return {path.name: content for path, content in written.items()}
        return _scaffold_integration_tests(names)

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs and produce tests."""
        # Get role-specific prompt
        role_prompt = self.get_role_prompt()

        # Create a prompt for the LLM
        prompt = f"""
        {role_prompt}

        You are a testing expert. Your task is to create comprehensive tests.

        Project context:
        {inputs.get('context', '')}

        Specifications:
        {inputs.get('specifications', '')}

        Create comprehensive tests with the following sections:
        1. BDD feature files
        2. Unit tests
        3. Integration tests
        4. Performance tests
        5. Security tests
        """

        # Generate the tests using the LLM port
        tests = self.generate_text(prompt)

        # Scaffold placeholder integration tests if names are provided
        integration_names = inputs.get("integration_test_names", [])
        output_dir_input = inputs.get(
            "integration_output_dir", "tests/integration/generated_tests"
        )
        output_dir = Path(output_dir_input)
        integration_tests = self.scaffold_integration_tests(
            integration_names, output_dir=output_dir
        )

        # Create a WSDE with the tests
        test_wsde = None
        try:
            test_wsde = self.create_wsde(
                content=tests,
                content_type="text",
                metadata={
                    "agent": self.name,
                    "role": self.current_role,
                    "type": "tests",
                },
            )
        except Exception as e:
            logger.error(f"Error creating WSDE: {str(e)}")

        return {
            "tests": tests,
            "wsde": test_wsde,
            "agent": self.name,
            "role": self.current_role,
            "integration_tests": integration_tests,
        }

    def get_capabilities(self) -> List[str]:
        """Get the capabilities of this agent."""
        capabilities = super().get_capabilities()
        if not capabilities:
            capabilities = [
                "create_bdd_features",
                "create_unit_tests",
                "create_integration_tests",
                "create_performance_tests",
                "create_security_tests",
            ]
        return capabilities
