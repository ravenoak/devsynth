"""Test agent for the DevSynth system."""

from pathlib import Path
from typing import Any, Dict, List

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

from .base import BaseAgent

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError


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
            Dictionary mapping filenames to placeholder test content.
        """
        import textwrap

        template = textwrap.dedent(
            '''
            """Scaffold integration test for {name}."""

            import pytest

            pytestmark = pytest.mark.skip(
                reason="Integration test for {name} not yet implemented"
            )


            def test_{name}():
                """Integration test scaffold for {name}."""
                pass
            '''
        )

        placeholders: Dict[str, str] = {}
        names = test_names or ["placeholder"]
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
        for name in names:
            safe_name = name.strip().lower().replace(" ", "_")
            filename = f"test_{safe_name}.py"
            content = template.format(name=safe_name)
            placeholders[filename] = content
            if output_dir:
                (output_dir / filename).write_text(content)
        return placeholders

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
        output_dir = Path("tests/integration/generated_tests")
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
