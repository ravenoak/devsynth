"""Tool registry for agent functions."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Sequence

from devsynth.agents.sandbox import sandboxed

from devsynth.logging_setup import DevSynthLogger
from devsynth.testing.run_tests import run_tests

logger = DevSynthLogger(__name__)


class ToolRegistry:
    """Registry mapping tool names to callables and metadata."""

    def __init__(self) -> None:
        """Initialize the tool registry."""
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        func: Callable[..., Any],
        description: str,
        parameters: Dict[str, Any],
        *,
        allow_shell: bool = False,
    ) -> None:
        """Register a tool with its callable and metadata.

        Tools are automatically wrapped so they execute inside a sandbox that
        restricts file system access to the project directory and blocks shell
        command execution unless ``allow_shell`` is ``True``.
        """
        wrapped = sandboxed(func, allow_shell=allow_shell)
        self._tools[name] = {
            "func": wrapped,
            "description": description,
            "parameters": parameters,
        }
        logger.debug("Registered tool %s", name)

    def get(self, name: str) -> Optional[Callable[..., Any]]:
        """Return the callable for a registered tool."""
        tool = self._tools.get(name)
        return tool["func"] if tool else None

    def get_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Return metadata for a registered tool."""
        tool = self._tools.get(name)
        if tool:
            return {
                "description": tool["description"],
                "parameters": tool["parameters"],
            }
        return None

    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """Return a copy of all registered tools and metadata."""
        return self._tools.copy()


# Global registry instance
_tool_registry = ToolRegistry()

# Export for direct import
tool_registry = _tool_registry


def get_tool_registry() -> ToolRegistry:
    """Return the global tool registry."""
    return _tool_registry


def run_tests_tool(
    target: str = "unit-tests",
    speed_categories: Optional[Sequence[str]] = None,
    verbose: bool = False,
    report: bool = False,
    parallel: bool = True,
    segment: bool = False,
    segment_size: int = 50,
) -> Dict[str, Any]:
    """Execute pytest tests and return the result.

    Args:
        target: Test target to execute (e.g., ``unit-tests``).
        speed_categories: Optional sequence of speed markers to filter tests.
        verbose: Show verbose output when running tests.
        report: Generate an HTML report for the test run.
        parallel: Run tests in parallel using ``pytest-xdist``.
        segment: Run tests in smaller batches.
        segment_size: Number of tests per batch when ``segment`` is ``True``.

    Returns:
        A dictionary containing ``success`` (bool) and ``output`` (str).
    """

    logger.debug(
        "Running tests with target=%s, speed_categories=%s", target, speed_categories
    )
    success, output = run_tests(
        target=target,
        speed_categories=speed_categories,
        verbose=verbose,
        report=report,
        parallel=parallel,
        segment=segment,
        segment_size=segment_size,
    )
    return {"success": success, "output": output}


_tool_registry.register(
    "run_tests",
    run_tests_tool,
    description="Run the project's pytest suites and return their output.",
    parameters={
        "type": "object",
        "properties": {
            "target": {
                "type": "string",
                "description": "Test target to run (unit-tests, integration-tests, behavior-tests, all-tests)",
            },
            "speed_categories": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional speed markers to filter tests",
            },
            "verbose": {
                "type": "boolean",
                "description": "Show verbose output",
            },
            "report": {
                "type": "boolean",
                "description": "Generate an HTML report",
            },
            "parallel": {
                "type": "boolean",
                "description": "Run tests in parallel",
            },
            "segment": {
                "type": "boolean",
                "description": "Run tests in batches",
            },
            "segment_size": {
                "type": "integer",
                "description": "Batch size when segmenting tests",
            },
        },
        "required": [],
    },
    allow_shell=True,
)
