"""Test agent for the DevSynth system."""

import os
import re
import subprocess
import sys
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


def scaffold_integration_tests(test_names: list[str]) -> dict[str, str]:
    """Public hook for generating placeholder integration test modules.

    This function re-exports :func:`devsynth.testing.generation.scaffold_integration_tests`
    so callers can generate integration test scaffolds without instantiating
    :class:`TestAgent`. The generated scaffolds include a simple passing
    assertion so they execute successfully out of the box.
    """

    return _scaffold_integration_tests(test_names)


def write_scaffolded_tests(directory: Path, test_names: list[str]) -> dict[Path, str]:
    """Public hook for writing placeholder integration test modules to disk."""

    return _write_scaffolded_tests(directory, test_names)


class TestAgent(BaseAgent):
    """Agent responsible for creating tests (BDD and unit tests)."""

    # Avoid pytest collecting this agent class as a test case
    __test__ = False

    def scaffold_integration_tests(
        self, test_names: list[str], output_dir: Path | None = None
    ) -> dict[str, str]:
        """Create placeholder integration test modules and optionally write them.

        The generated scaffolds contain an executable assertion, providing a
        lightweight check that the test runner is wired correctly while clearly
        indicating where real integration coverage should be added.

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

    def scaffold_integration_scenarios(
        self, scenarios: list[Any], output_dir: Path | None = None
    ) -> dict[str, str]:
        """Create placeholder tests for the given integration scenarios.

        Each scaffolded test includes a trivial passing assertion.

        Args:
            scenarios: Scenario descriptors or names.
            output_dir: Directory where test scaffolds should be written. If
                ``None`` the scaffolds are only returned.

        Returns:
            Mapping of file names to placeholder test content.
        """

        names: list[str] = []
        for scenario in scenarios or ["placeholder"]:
            if isinstance(scenario, dict):
                names.append(str(scenario.get("name", "scenario")))
            else:
                names.append(str(scenario))
        return self.scaffold_integration_tests(names, output_dir=output_dir)

    def run_generated_tests(self, directory: Path) -> str:
        """Run tests in ``directory`` and raise on failures.

        This helper executes the scaffolded tests so unmet requirements
        surface as errors.

        Args:
            directory: Location of the tests to run.

        Returns:
            Combined stdout and stderr from the test run.

        Raises:
            DevSynthError: If the tests fail.
        """

        # Ensure subprocess runs with stubbed/offline providers and without real LLM resources.
        # This prevents accidental network calls and enforces isolation per docs/tasks.md (Task 26/27)
        env = os.environ.copy()
        env.setdefault("DEVSYNTH_PROVIDER", "stub")
        env.setdefault("DEVSYNTH_OFFLINE", "true")
        # Explicitly disable real LLM resources unless the caller opts in
        env.setdefault("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "false")
        env.setdefault("DEVSYNTH_RESOURCE_OPENAI_AVAILABLE", "false")
        env.setdefault("DEVSYNTH_RESOURCE_LLM_PROVIDER_AVAILABLE", "false")

        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=str(directory),
            env=env,
            capture_output=True,
            text=True,
        )
        output = result.stdout + result.stderr
        if result.returncode != 0:
            raise DevSynthError(output)
        return output

    @staticmethod
    def _names_from_context(context: str) -> list[str]:
        """Derive integration test names from project context.

        The helper searches for tokens following ``module``, ``service``, or
        ``component`` keywords and returns the matched identifiers. This keeps
        heuristics lightweight while allowing callers to provide natural project
        descriptions.

        Args:
            context: Free-form project description.

        Returns:
            List of extracted identifiers suitable for scaffolding.
        """

        pattern = re.compile(
            r"([A-Za-z_][A-Za-z0-9_]*)\s*(?:module|service|component)|"
            r"(?:module|service|component)\s+([A-Za-z_][A-Za-z0-9_]*)",
            re.IGNORECASE,
        )
        names: list[str] = []
        for before, after in pattern.findall(context):
            candidate = before or after
            if candidate:
                names.append(candidate)
        return names

    def process(self, inputs: dict[str, Any]) -> dict[str, Any]:
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

        # Scaffold placeholder integration tests if names, scenarios, or context are provided
        integration_names = inputs.get("integration_test_names", [])
        context_names = self._names_from_context(inputs.get("context", ""))
        if context_names:
            integration_names.extend(
                name for name in context_names if name not in integration_names
            )
        scenarios = inputs.get("integration_scenarios", [])
        output_dir_input = inputs.get(
            "integration_output_dir", "tests/integration/generated_tests"
        )
        output_dir = Path(output_dir_input)
        integration_tests: dict[str, str] = {}

        # Handle multi-module projects by creating a scaffolded test for each module.
        modules = inputs.get("modules", [])
        for module in modules:
            module_path = Path(str(module).replace(".", "/"))
            module_dir = output_dir / module_path
            written = self.scaffold_integration_tests(
                [module_path.name], output_dir=module_dir
            )
            integration_tests.update(
                {str(module_path / name): content for name, content in written.items()}
            )

        if integration_names:
            integration_tests.update(
                self.scaffold_integration_tests(
                    integration_names, output_dir=output_dir
                )
            )
        if scenarios:
            integration_tests.update(
                self.scaffold_integration_scenarios(scenarios, output_dir=output_dir)
            )
        if not integration_tests:
            integration_tests = self.scaffold_integration_tests(
                [], output_dir=output_dir
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

    def get_capabilities(self) -> list[str]:
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
