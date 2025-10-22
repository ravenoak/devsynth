"""Tool registry for agent functions."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from typing import Literal, Optional, Protocol, TypeAlias, TypedDict

from devsynth.agents.sandbox import sandboxed
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger
from devsynth.testing.run_tests import PytestCovMissingError, run_tests

logger = DevSynthLogger(__name__)


JSONPrimitive: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONPrimitive | Sequence["JSONValue"] | Mapping[str, "JSONValue"]
JSONMapping: TypeAlias = Mapping[str, JSONValue]
MutableJSONMapping: TypeAlias = MutableMapping[str, JSONValue]
ToolResponse: TypeAlias = MutableJSONMapping


class ToolCallable(Protocol):
    """Callable protocol for registered tools."""

    def __call__(self, *args: object, **kwargs: object) -> ToolResponse: ...


@dataclass(frozen=True)
class RegisteredTool:
    """Dataclass storing the callable and schema metadata for a tool."""

    func: ToolCallable
    description: str
    parameters: JSONMapping


class ToolMetadata(TypedDict):
    """Metadata exposed for registered tools."""

    description: str
    parameters: JSONMapping


class OpenAIFunctionSpec(TypedDict):
    """Function metadata compatible with OpenAI tool calling."""

    name: str
    description: str
    parameters: JSONMapping


class OpenAIToolDefinition(TypedDict):
    """Tool definition compatible with OpenAI function-calling APIs."""

    type: Literal["function"]
    function: OpenAIFunctionSpec


class ToolRegistry:
    """Registry mapping tool names to callables and metadata."""

    def __init__(self) -> None:
        """Initialize the tool registry."""
        self._tools: dict[str, RegisteredTool] = {}

    def register(
        self,
        name: str,
        func: ToolCallable,
        description: str,
        parameters: JSONMapping,
        *,
        allow_shell: bool = False,
    ) -> None:
        """Register a tool with its callable and metadata.

        Tools are automatically wrapped so they execute inside a sandbox that
        restricts file system access to the project directory and blocks shell
        command execution unless ``allow_shell`` is ``True``.
        """
        wrapped = sandboxed(func, allow_shell=allow_shell)
        self._tools[name] = RegisteredTool(
            func=wrapped,
            description=description,
            parameters=parameters,
        )
        logger.debug("Registered tool %s", name)

    def get(self, name: str) -> Optional[ToolCallable]:
        """Return the callable for a registered tool."""
        tool = self._tools.get(name)
        return tool.func if tool else None

    def get_metadata(self, name: str) -> Optional[ToolMetadata]:
        """Return metadata for a registered tool."""
        tool = self._tools.get(name)
        if tool:
            return {"description": tool.description, "parameters": tool.parameters}
        return None

    def list_tools(self) -> dict[str, RegisteredTool]:
        """Return a copy of all registered tools and metadata."""
        return dict(self._tools)

    def export_for_openai(self) -> Sequence[OpenAIToolDefinition]:
        """Return tools formatted for OpenAI function calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": meta.description,
                    "parameters": meta.parameters,
                },
            }
            for name, meta in self._tools.items()
        ]


# Global registry instance
_tool_registry = ToolRegistry()

# Export for direct import
tool_registry = _tool_registry


def get_tool_registry() -> ToolRegistry:
    """Return the global tool registry."""
    return _tool_registry


def get_openai_tools() -> Sequence[OpenAIToolDefinition]:
    """Export registered tools in OpenAI function-call format."""
    return _tool_registry.export_for_openai()


class _CaptureBridge(UXBridge):
    """Minimal UX bridge capturing messages for tool output."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    # The following methods are placeholders; they are not used by the tools
    # that rely on this bridge but must be implemented to satisfy the
    # :class:`UXBridge` abstract interface.
    def ask_question(
        self,
        message: str,
        *,
        choices: Optional[Sequence[str]] = None,
        default: Optional[str] = None,
        show_default: bool = True,
    ) -> str:  # pragma: no cover - interface stub
        return default or ""

    def confirm_choice(
        self, message: str, *, default: bool = False
    ) -> bool:  # pragma: no cover - interface stub
        return default

    def display_result(
        self, message: str, *, highlight: bool = False, message_type: str | None = None
    ) -> None:
        self.messages.append(message)


def alignment_metrics_tool(
    path: str = ".",
    metrics_file: str = ".devsynth/alignment_metrics.json",
    output: Optional[str] = None,
) -> ToolResponse:
    """Collect alignment metrics and return them.

    Args:
        path: Path to the project directory.
        metrics_file: File path to store historical metrics.
        output: Optional path for a generated Markdown report.

    Returns:
        A dictionary with ``success`` and ``metrics`` keys.
    """

    logger.debug(
        "Collecting alignment metrics for path=%s, metrics_file=%s", path, metrics_file
    )

    try:
        from devsynth.application.cli.commands.align_cmd import get_all_files
        from devsynth.application.cli.commands.alignment_metrics_cmd import (
            calculate_alignment_coverage,
            calculate_alignment_issues,
            generate_metrics_report,
            load_historical_metrics,
            save_metrics,
        )

        os.makedirs(os.path.dirname(metrics_file), exist_ok=True)

        files = get_all_files(path)
        existing_files = [f for f in files if os.path.isfile(f)]

        coverage_metrics = calculate_alignment_coverage(existing_files)
        issues_metrics = calculate_alignment_issues(existing_files)
        metrics: dict[str, float | int] = {
            **coverage_metrics,
            **issues_metrics,
        }

        historical_metrics = load_historical_metrics(metrics_file)
        save_metrics(metrics, metrics_file, historical_metrics)

        if output:
            generate_metrics_report(metrics, historical_metrics, output)

        return {"success": True, "metrics": metrics}

    except (ImportError, OSError, ValueError) as exc:  # pragma: no cover - defensive
        logger.error("Error collecting alignment metrics: %s", exc)
        return {"success": False, "error": str(exc)}


def run_tests_tool(
    target: str = "unit-tests",
    speed_categories: Optional[Sequence[str]] = None,
    verbose: bool = False,
    report: bool = False,
    parallel: bool = True,
    segment: bool = False,
    segment_size: int = 50,
) -> ToolResponse:
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
    try:
        success, output = run_tests(
            target=target,
            speed_categories=speed_categories,
            verbose=verbose,
            report=report,
            parallel=parallel,
            segment=segment,
            segment_size=segment_size,
        )
    except PytestCovMissingError as exc:
        return {"success": False, "error": str(exc), "output": str(exc)}
    return {"success": success, "output": output}


def security_audit_tool(
    skip_static: bool = False,
    skip_safety: bool = False,
    skip_secrets: bool = False,
    skip_owasp: bool = False,
) -> ToolResponse:
    """Run security audit checks and return collected output."""

    logger.debug(
        "Running security audit with skips: static=%s safety=%s secrets=%s owasp=%s",
        skip_static,
        skip_safety,
        skip_secrets,
        skip_owasp,
    )
    bridge = _CaptureBridge()
    try:
        from devsynth.application.cli.commands.security_audit_cmd import (
            security_audit_cmd,
        )

        security_audit_cmd(
            skip_static=skip_static,
            skip_safety=skip_safety,
            skip_secrets=skip_secrets,
            skip_owasp=skip_owasp,
            bridge=bridge,
        )
        return {"success": True, "output": "\n".join(bridge.messages)}
    except (ImportError, RuntimeError) as exc:  # pragma: no cover - defensive
        logger.error("Security audit failed: %s", exc)
        return {
            "success": False,
            "error": str(exc),
            "output": "\n".join(bridge.messages),
        }


# Feature: Doctor command
# Feature: DevSynth Doctor
# Feature: Doctor Command
# Feature: Doctor command with missing environment variables
def doctor_tool(config_dir: str = "config", quick: bool = False) -> ToolResponse:
    """Validate configuration files and environment setup."""

    logger.debug("Running doctor on config_dir=%s quick=%s", config_dir, quick)
    bridge = _CaptureBridge()
    try:
        from devsynth.application.cli.commands.doctor_cmd import doctor_cmd

        doctor_cmd(config_dir=config_dir, quick=quick, bridge=bridge)
        return {"success": True, "output": "\n".join(bridge.messages)}
    except SystemExit as exc:  # pragma: no cover - propagate failure but capture output
        return {
            "success": False,
            "error": str(exc),
            "output": "\n".join(bridge.messages),
        }
    except (ImportError, RuntimeError) as exc:  # pragma: no cover - defensive
        logger.error("Doctor command failed: %s", exc)
        return {
            "success": False,
            "error": str(exc),
            "output": "\n".join(bridge.messages),
        }


_tool_registry.register(
    "alignment_metrics",
    alignment_metrics_tool,
    description="Collect alignment coverage metrics and return them.",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Project directory to analyze",
            },
            "metrics_file": {
                "type": "string",
                "description": "Path to store historical metrics",
            },
            "output": {
                "type": "string",
                "description": "Optional path for a Markdown report",
            },
        },
        "required": [],
    },
)


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

_tool_registry.register(
    "security_audit",
    security_audit_tool,
    description=(
        "Run security audit checks including static analysis and "
        "dependency scanning."
    ),
    parameters={
        "type": "object",
        "properties": {
            "skip_static": {
                "type": "boolean",
                "description": "Skip Bandit static analysis",
            },
            "skip_safety": {
                "type": "boolean",
                "description": "Skip dependency vulnerability scan",
            },
            "skip_secrets": {
                "type": "boolean",
                "description": "Skip secrets scanning",
            },
            "skip_owasp": {
                "type": "boolean",
                "description": "Skip OWASP Dependency Check",
            },
        },
        "required": [],
    },
    allow_shell=True,
)

_tool_registry.register(
    "doctor",
    doctor_tool,
    description=("Validate configuration files and environment setup."),
    parameters={
        "type": "object",
        "properties": {
            "config_dir": {
                "type": "string",
                "description": "Directory containing configuration files",
            },
            "quick": {
                "type": "boolean",
                "description": "Run quick pytest checks",
            },
        },
        "required": [],
    },
    allow_shell=True,
)
