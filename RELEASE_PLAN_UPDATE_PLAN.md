# DevSynth Release Plan Update: Comprehensive Feature Implementation from 0.1.0 to 1.0.0

## Executive Summary

This document outlines a comprehensive plan to update the DevSynth release strategy to include several crucial new features: Shell Command Execution for running test suites, Model-Context Protocol (MCP) integration for connecting to external tools and data sources, and a unified Metrics and Analytics System. These features, along with other planned enhancements, will significantly improve DevSynth's capabilities and user experience as it progresses from version 0.1.0 to 1.0.0. The plan includes detailed implementation approaches, documentation alignment strategies, and testing methodologies, all following DevSynth's hexagonal architecture and best practices.

## Current State Analysis

### Project Status

DevSynth is currently in pre-release development (version 0.1.0) with a structured development approach organized into five phases:

1. **Foundation Stabilization**: Core architecture, EDRR framework, and WSDE agent collaboration
2. **CLI UX Polishing & Web UI Integration**: CLI experience and preliminary Web UI
3. **Multi-Agent Collaboration & EDRR Enhancements**: Team collaboration features and EDRR pipeline
4. **Testing, Documentation & Final Polish**: Test coverage and documentation
5. **Release Readiness & Deployment**: Final verification, packaging, and release CI

The project follows a hexagonal architecture with clear separation between domain, application, adapters, and ports layers. It implements a Worker Self-Directed Enterprise (WSDE) model for multi-agent collaboration and an Expand, Differentiate, Refine, Retrospect (EDRR) framework for adaptive project ingestion.

### Feature Gap Analysis

Based on the examination of the codebase and documentation, the following gaps have been identified:

1. **Shell Command Execution**:
   - Currently, subprocess is used in various parts of the codebase (documentation_fetcher.py, test_metrics_cmd.py) for specific purposes
   - No dedicated shell command execution port or adapter exists
   - No standardized way to run external test suites or other shell commands
   - No integration with the CLI for running custom shell commands

2. **Model-Context Protocol (MCP) Integration**:
   - No implementation of MCP clients to connect to external MCP servers
   - No implementation of MCP servers to expose DevSynth functionality to other applications
   - Missing integration with DevSynth's existing architecture
   - No configuration options for MCP client/server connections
   - No documentation on how to use MCP with DevSynth

3. **Unified Metrics and Analytics System**:
   - Several isolated metrics implementations exist across different components
   - No central metrics registry to serve as a single source of truth
   - No comprehensive categorization of metrics (performance, efficacy, efficiency, resource consumption)
   - Limited user-facing features for metrics visualization and analysis
   - No integration with time-series databases for historical analysis

4. **Documentation Alignment**:
   - Documentation is spread across multiple directories (docs/, release_plan/)
   - Some documentation may be outdated or inconsistent
   - No comprehensive documentation for the new features

## Implementation Plan

### 1. Shell Command Execution

#### 1.1 Shell Command Port and Adapter

Following DevSynth's hexagonal architecture, we'll create a new port and adapter for shell command execution:

```python
# src/devsynth/ports/shell_command_port.py
from typing import Dict, List, Optional, Union, Any

class ShellCommandPort:
    """Port for executing shell commands."""

    def execute(self, 
                command: Union[str, List[str]], 
                cwd: Optional[str] = None, 
                env: Optional[Dict[str, str]] = None,
                capture_output: bool = True,
                check: bool = True) -> Dict[str, Any]:
        """Execute a shell command.

        Args:
            command: Command to execute (string or list of arguments)
            cwd: Working directory for command execution
            env: Environment variables for command execution
            capture_output: Whether to capture command output
            check: Whether to check return code

        Returns:
            Dictionary with execution results
        """
        pass
```

```python
# src/devsynth/adapters/shell/subprocess_adapter.py
import subprocess
import shlex
from typing import Dict, List, Optional, Union, Any
import os

from ...ports.shell_command_port import ShellCommandPort
from ...logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)

class SubprocessShellAdapter(ShellCommandPort):
    """Shell command execution adapter using subprocess."""

    def execute(self, 
                command: Union[str, List[str]], 
                cwd: Optional[str] = None, 
                env: Optional[Dict[str, str]] = None,
                capture_output: bool = True,
                check: bool = True) -> Dict[str, Any]:
        """Execute a shell command using subprocess.

        Args:
            command: Command to execute (string or list of arguments)
            cwd: Working directory for command execution
            env: Environment variables for command execution
            capture_output: Whether to capture command output
            check: Whether to check return code

        Returns:
            Dictionary with execution results
        """
        try:
            # Prepare command
            if isinstance(command, str):
                cmd_list = shlex.split(command)
            else:
                cmd_list = command

            # Prepare environment
            exec_env = os.environ.copy()
            if env:
                exec_env.update(env)

            # Execute command
            logger.info(f"Executing command: {' '.join(cmd_list)}")
            result = subprocess.run(
                cmd_list,
                cwd=cwd,
                env=exec_env,
                capture_output=capture_output,
                text=True,
                check=check
            )

            # Return results
            return {
                "success": True,
                "return_code": result.returncode,
                "stdout": result.stdout if capture_output else None,
                "stderr": result.stderr if capture_output else None,
                "command": cmd_list
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"Command execution failed: {e}")
            return {
                "success": False,
                "return_code": e.returncode,
                "stdout": e.stdout if capture_output else None,
                "stderr": e.stderr if capture_output else None,
                "error": str(e),
                "command": cmd_list
            }
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
```

#### 1.2 Test Suite Runner Service

Create a service for running different types of test suites:

```python
# src/devsynth/application/testing/test_suite_runner.py
from typing import Dict, List, Optional, Any
import os
from pathlib import Path

from ...ports.shell_command_port import ShellCommandPort
from ...logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)

class TestSuiteRunner:
    """Service for running different types of test suites."""

    def __init__(self, shell_command_port: ShellCommandPort):
        """Initialize the test suite runner.

        Args:
            shell_command_port: Port for executing shell commands
        """
        self.shell_command_port = shell_command_port

    def run_pytest(self, 
                  path: str = "tests", 
                  markers: Optional[List[str]] = None,
                  options: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run pytest test suite.

        Args:
            path: Path to test directory or file
            markers: Pytest markers to filter tests
            options: Additional pytest options

        Returns:
            Dictionary with test results
        """
        cmd = ["pytest", path]

        # Add markers if specified
        if markers:
            for marker in markers:
                cmd.append(f"-m {marker}")

        # Add options if specified
        if options:
            cmd.extend(options)

        # Run command
        result = self.shell_command_port.execute(cmd)

        # Parse test results
        if result["success"]:
            # Extract test summary from output
            summary = self._parse_pytest_output(result["stdout"])
            result.update(summary)

        return result

    def run_unittest(self, 
                    path: str = "tests", 
                    pattern: str = "test*.py",
                    options: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run unittest test suite.

        Args:
            path: Path to test directory
            pattern: Test file pattern
            options: Additional unittest options

        Returns:
            Dictionary with test results
        """
        cmd = ["python", "-m", "unittest", "discover", "-s", path, "-p", pattern]

        # Add options if specified
        if options:
            cmd.extend(options)

        # Run command
        result = self.shell_command_port.execute(cmd)

        return result

    def run_custom_command(self, command: str) -> Dict[str, Any]:
        """Run a custom test command.

        Args:
            command: Custom test command

        Returns:
            Dictionary with test results
        """
        return self.shell_command_port.execute(command)

    def _parse_pytest_output(self, output: str) -> Dict[str, Any]:
        """Parse pytest output to extract test summary.

        Args:
            output: Pytest output

        Returns:
            Dictionary with test summary
        """
        summary = {
            "tests_total": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_skipped": 0
        }

        # Simple parsing logic - can be enhanced for more detailed results
        if output:
            lines = output.splitlines()
            for line in lines:
                if "passed" in line and "failed" in line and "skipped" in line:
                    parts = line.split()
                    for part in parts:
                        if "passed" in part:
                            summary["tests_passed"] = int(part.split("passed")[0])
                        elif "failed" in part:
                            summary["tests_failed"] = int(part.split("failed")[0])
                        elif "skipped" in part:
                            summary["tests_skipped"] = int(part.split("skipped")[0])

            summary["tests_total"] = summary["tests_passed"] + summary["tests_failed"] + summary["tests_skipped"]

        return summary
```

#### 1.3 CLI Integration

Enhance the existing `run-pipeline` command to use the new test suite runner:

```python
# src/devsynth/application/cli/cli_commands.py (update)
from ..testing.test_suite_runner import TestSuiteRunner
from ...adapters.shell.subprocess_adapter import SubprocessShellAdapter

def run_pipeline_cmd(
    target: Optional[str] = None,
    report: Optional[Dict[str, Any]] = None,
    command: Optional[str] = None,  # New parameter for custom command
    *,
    bridge: Optional[UXBridge] = None,
) -> None:
    """Run the generated code or a specific target.

    This command executes the generated code or a specific target, such as unit tests.
    It can also persist a report with the results.

    Args:
        target: Execution target (e.g. "unit-tests", "integration-tests", "all")
        report: Optional report data that should be persisted with pipeline results
        command: Custom shell command to execute
        bridge: Optional UX bridge for interaction

    Examples:
        Run the default pipeline:
        ```
        devsynth run-pipeline
        ```

        Run a specific target:
        ```
        devsynth run-pipeline --target unit-tests
        ```

        Run a custom command:
        ```
        devsynth run-pipeline --command "pytest tests/unit -v"
        ```
    """
    bridge = _resolve_bridge(bridge)
    try:
        # Check required services
        if not _check_services(bridge):
            return

        # Initialize test suite runner
        shell_adapter = SubprocessShellAdapter()
        test_runner = TestSuiteRunner(shell_adapter)

        # If custom command is provided, use it
        if command:
            bridge.display_result(f"[blue]Running custom command: {command}[/blue]")
            result = test_runner.run_custom_command(command)

            if result["success"]:
                bridge.display_result(f"[green]Command executed successfully.[/green]")
                if result.get("stdout"):
                    bridge.display_result(f"[blue]Output:[/blue]\n{result['stdout']}")
            else:
                bridge.display_result(f"[red]Command execution failed.[/red]")
                if result.get("stderr"):
                    bridge.display_result(f"[red]Error:[/red]\n{result['stderr']}")
            return

        # Validate target if provided
        valid_targets = ["unit-tests", "integration-tests", "behavior-tests", "all"]
        if target and target not in valid_targets:
            bridge.display_result(
                f"[yellow]Warning: '{target}' is not a standard target. Valid targets are: {', '.join(valid_targets)}[/yellow]"
            )
            if not bridge.confirm_choice(f"Continue with target '{target}'?", default=True):
                return

        # Execute command based on target
        bridge.display_result(f"[blue]Running {'target: ' + target if target else 'default pipeline'}...[/blue]")

        if target == "unit-tests" or target == "all":
            bridge.display_result("[blue]Running unit tests...[/blue]")
            unit_result = test_runner.run_pytest("tests/unit", options=["-v"])
            _display_test_results(bridge, "Unit Tests", unit_result)

        if target == "integration-tests" or target == "all":
            bridge.display_result("[blue]Running integration tests...[/blue]")
            integration_result = test_runner.run_pytest("tests/integration", options=["-v"])
            _display_test_results(bridge, "Integration Tests", integration_result)

        if target == "behavior-tests" or target == "all":
            bridge.display_result("[blue]Running behavior tests...[/blue]")
            behavior_result = test_runner.run_pytest("tests/behavior", options=["-v"])
            _display_test_results(bridge, "Behavior Tests", behavior_result)

        if not target:
            # Default pipeline - use workflow system
            result = workflows.execute_command(
                "run-pipeline", {"target": target, "report": report}
            )

            # Handle result
            if result.get("success"):
                bridge.display_result(f"[green]Pipeline execution complete.[/green]")
                if "output" in result:
                    bridge.display_result(f"[blue]Output:[/blue]\n{result['output']}")
            else:
                _handle_error(bridge, result)

    except Exception as err:  # pragma: no cover - defensive
        _handle_error(bridge, err)

def _display_test_results(bridge: UXBridge, test_type: str, result: Dict[str, Any]) -> None:
    """Display test results in a formatted way.

    Args:
        bridge: UX bridge for interaction
        test_type: Type of tests (e.g. "Unit Tests")
        result: Test results dictionary
    """
    if result["success"]:
        if "tests_total" in result:
            bridge.display_result(
                f"[green]{test_type} Results:[/green] "
                f"Total: {result['tests_total']}, "
                f"Passed: {result['tests_passed']}, "
                f"Failed: {result['tests_failed']}, "
                f"Skipped: {result['tests_skipped']}"
            )
        else:
            bridge.display_result(f"[green]{test_type} completed successfully.[/green]")
    else:
        bridge.display_result(f"[red]{test_type} failed.[/red]")
        if result.get("stderr"):
            bridge.display_result(f"[red]Error:[/red]\n{result['stderr']}")
```

### 2. MCP Server Integration

#### 2.1 Provider System Update

Update the provider system to include MCP Server support:

```python
# src/devsynth/adapters/provider_system.py (update)

class ProviderType(Enum):
    """Enum for supported LLM providers."""

    OPENAI = "openai"
    LM_STUDIO = "lm_studio"
    MCP = "mcp"  # Add MCP provider type
```

```python
# src/devsynth/adapters/providers/mcp_provider.py
from typing import Dict, List, Optional, Any, Union
import os
import json
import httpx
from pydantic import BaseModel, Field

from ...domain.interfaces.provider import ProviderInterface, ProviderResponse
from ...logging_setup import DevSynthLogger
from ...security.tls import TLSConfig

# Import the official MCP Python SDK if available
try:
    import mcp
    HAS_MCP_SDK = True
except ImportError:
    HAS_MCP_SDK = False
    logger.warning("MCP SDK not found. Using fallback HTTP implementation.")

logger = DevSynthLogger(__name__)

class MCPMessage(BaseModel):
    """Message format for MCP protocol."""
    role: str
    content: str
    name: Optional[str] = None

class MCPRequest(BaseModel):
    """Request format for MCP protocol."""
    model: str
    messages: List[MCPMessage]
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False

class MCPProvider(BaseProvider):
    """Provider adapter for MCP (Model-Context Protocol) servers.

    This provider supports two implementation modes:
    1. Native SDK mode: Uses the official MCP Python SDK (preferred)
    2. HTTP mode: Uses direct HTTP requests as a fallback
    """

    def __init__(self, 
                 endpoint: Optional[str] = None, 
                 api_key: Optional[str] = None,
                 model: Optional[str] = None,
                 timeout: int = 120,
                 use_sdk: Optional[bool] = None,
                 tls_config: TLSConfig | None = None):
        """Initialize the MCP provider.

        Args:
            endpoint: MCP server endpoint URL
            api_key: API key for authentication
            model: Model to use
            timeout: Request timeout in seconds
            use_sdk: Whether to use the MCP SDK (if available)
            tls_config: TLS configuration
        """
        super().__init__(tls_config=tls_config, endpoint=endpoint, api_key=api_key, model=model)
        self.endpoint = endpoint or os.environ.get("MCP_SERVER_ENDPOINT", "http://localhost:8000")
        self.api_key = api_key or os.environ.get("MCP_SERVER_API_KEY")
        self.model = model or os.environ.get("MCP_SERVER_MODEL", "claude-3-opus-20240229")
        self.timeout = timeout

        # Determine whether to use the SDK
        self.use_sdk = use_sdk if use_sdk is not None else HAS_MCP_SDK

        # Initialize HTTP headers for fallback mode
        self.headers = {"Content-Type": "application/json"}
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

        # Initialize SDK client if using SDK mode
        if self.use_sdk and HAS_MCP_SDK:
            try:
                self.client = mcp.Client(
                    base_url=self.endpoint,
                    api_key=self.api_key,
                    timeout=self.timeout
                )
                logger.info(f"Initialized MCP SDK client for endpoint: {self.endpoint}")
            except Exception as e:
                logger.error(f"Failed to initialize MCP SDK client: {e}")
                self.use_sdk = False

    def complete(self, 
                prompt: str, 
                system_prompt: Optional[str] = None,
                temperature: float = 0.7,
                max_tokens: int = 2000) -> str:
        """Generate a completion using MCP server.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate

        Returns:
            str: Generated completion

        Raises:
            ProviderError: If API call fails
        """
        try:
            # Prepare messages
            messages = []
            if system_prompt:
                messages.append(MCPMessage(role="system", content=system_prompt))
            messages.append(MCPMessage(role="user", content=prompt))

            if self.use_sdk and hasattr(self, 'client'):
                # Use the MCP SDK if available
                logger.info(f"Using MCP SDK to send request to: {self.endpoint}")
                try:
                    # Convert our messages to SDK format
                    sdk_messages = [
                        mcp.Message(role=msg.role, content=msg.content, name=msg.name)
                        for msg in messages
                    ]

                    # Send request using SDK
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=sdk_messages,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )

                    # Extract content from SDK response
                    content = response.choices[0].message.content
                    return content

                except Exception as sdk_error:
                    logger.error(f"Error using MCP SDK: {sdk_error}. Falling back to HTTP implementation.")
                    # Fall back to HTTP implementation

            # Fallback: Use direct HTTP requests
            # Prepare request
            request = MCPRequest(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Send request
            logger.info(f"Sending HTTP request to MCP server: {self.endpoint}")
            with httpx.Client(timeout=self.timeout, **self.tls_config.as_requests_kwargs()) as client:
                response = client.post(
                    f"{self.endpoint}/v1/chat/completions",
                    headers=self.headers,
                    content=request.model_dump_json()
                )

            # Check response
            response.raise_for_status()
            result = response.json()

            # Extract content
            content = result["choices"][0]["message"]["content"]

            return content

        except Exception as e:
            logger.error(f"Error querying MCP server: {e}")
            raise ProviderError(f"MCP server error: {e}")

    async def acomplete(self,
                       prompt: str,
                       system_prompt: Optional[str] = None,
                       temperature: float = 0.7,
                       max_tokens: int = 2000) -> str:
        """Asynchronously generate a completion using MCP server.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate

        Returns:
            str: Generated completion

        Raises:
            ProviderError: If API call fails
        """
        try:
            # Prepare messages
            messages = []
            if system_prompt:
                messages.append(MCPMessage(role="system", content=system_prompt))
            messages.append(MCPMessage(role="user", content=prompt))

            if self.use_sdk and hasattr(self, 'client') and hasattr(self.client, 'achat'):
                # Use the MCP SDK if available and supports async
                logger.info(f"Using MCP SDK to send async request to: {self.endpoint}")
                try:
                    # Convert our messages to SDK format
                    sdk_messages = [
                        mcp.Message(role=msg.role, content=msg.content, name=msg.name)
                        for msg in messages
                    ]

                    # Send request using SDK async method if available
                    response = await self.client.achat.completions.create(
                        model=self.model,
                        messages=sdk_messages,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )

                    # Extract content from SDK response
                    content = response.choices[0].message.content
                    return content

                except (AttributeError, Exception) as sdk_error:
                    logger.error(f"Error using MCP SDK async: {sdk_error}. Falling back to HTTP implementation.")
                    # Fall back to HTTP implementation

            # Fallback: Use direct HTTP requests
            # Prepare request
            request = MCPRequest(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Send request
            logger.info(f"Sending async HTTP request to MCP server: {self.endpoint}")
            async with httpx.AsyncClient(timeout=self.timeout, **self.tls_config.as_requests_kwargs()) as client:
                response = await client.post(
                    f"{self.endpoint}/v1/chat/completions",
                    headers=self.headers,
                    content=request.model_dump_json()
                )

            # Check response
            response.raise_for_status()
            result = response.json()

            # Extract content
            content = result["choices"][0]["message"]["content"]

            return content

        except Exception as e:
            logger.error(f"Error querying MCP server asynchronously: {e}")
            raise ProviderError(f"MCP server error: {e}")

    def embed(self, text: Union[str, List[str]]) -> List[List[float]]:
        """Generate embeddings using MCP server.

        Args:
            text: Input text or list of texts

        Returns:
            List[List[float]]: Embeddings

        Raises:
            ProviderError: If API call fails
        """
        try:
            # Prepare input
            if isinstance(text, str):
                text_list = [text]
            else:
                text_list = text

            if self.use_sdk and hasattr(self, 'client') and hasattr(self.client, 'embeddings'):
                # Use the MCP SDK if available
                logger.info(f"Using MCP SDK to get embeddings from: {self.endpoint}")
                try:
                    # Send request using SDK
                    response = self.client.embeddings.create(
                        model="embedding-model",  # Use appropriate embedding model
                        input=text_list
                    )

                    # Extract embeddings from SDK response
                    return [item.embedding for item in response.data]

                except Exception as sdk_error:
                    logger.error(f"Error using MCP SDK for embeddings: {sdk_error}. Falling back to HTTP implementation.")
                    # Fall back to HTTP implementation

            # Fallback: Use direct HTTP requests
            # Prepare request
            request = {
                "model": "embedding-model",  # Use appropriate embedding model
                "input": text_list
            }

            # Send request
            logger.info(f"Sending HTTP embedding request to MCP server: {self.endpoint}")
            with httpx.Client(timeout=self.timeout, **self.tls_config.as_requests_kwargs()) as client:
                response = client.post(
                    f"{self.endpoint}/v1/embeddings",
                    headers=self.headers,
                    json=request
                )

            # Check response
            response.raise_for_status()
            result = response.json()

            # Extract embeddings
            if "data" in result and len(result["data"]) > 0:
                return [item["embedding"] for item in result["data"]]
            else:
                raise ProviderError(f"Invalid embedding response format: {result}")

        except Exception as e:
            logger.error(f"Error getting embeddings from MCP server: {e}")
            raise ProviderError(f"MCP server embedding error: {e}")

    async def aembed(self, text: Union[str, List[str]]) -> List[List[float]]:
        """Asynchronously generate embeddings using MCP server.

        Args:
            text: Input text or list of texts

        Returns:
            List[List[float]]: Embeddings

        Raises:
            ProviderError: If API call fails
        """
        try:
            # Prepare input
            if isinstance(text, str):
                text_list = [text]
            else:
                text_list = text

            if self.use_sdk and hasattr(self, 'client') and hasattr(self.client, 'aembeddings'):
                # Use the MCP SDK if available and supports async
                logger.info(f"Using MCP SDK to get async embeddings from: {self.endpoint}")
                try:
                    # Send request using SDK async method if available
                    response = await self.client.aembeddings.create(
                        model="embedding-model",  # Use appropriate embedding model
                        input=text_list
                    )

                    # Extract embeddings from SDK response
                    return [item.embedding for item in response.data]

                except (AttributeError, Exception) as sdk_error:
                    logger.error(f"Error using MCP SDK for async embeddings: {sdk_error}. Falling back to HTTP implementation.")
                    # Fall back to HTTP implementation

            # Fallback: Use direct HTTP requests
            # Prepare request
            request = {
                "model": "embedding-model",  # Use appropriate embedding model
                "input": text_list
            }

            # Send request
            logger.info(f"Sending async HTTP embedding request to MCP server: {self.endpoint}")
            async with httpx.AsyncClient(timeout=self.timeout, **self.tls_config.as_requests_kwargs()) as client:
                response = await client.post(
                    f"{self.endpoint}/v1/embeddings",
                    headers=self.headers,
                    json=request
                )

            # Check response
            response.raise_for_status()
            result = response.json()

            # Extract embeddings
            if "data" in result and len(result["data"]) > 0:
                return [item["embedding"] for item in result["data"]]
            else:
                raise ProviderError(f"Invalid embedding response format: {result}")

        except Exception as e:
            logger.error(f"Error getting embeddings from MCP server asynchronously: {e}")
            raise ProviderError(f"MCP server embedding error: {e}")
```

#### 2.2 Provider Factory Update

Update the provider factory to include MCP provider:

```python
# src/devsynth/adapters/provider_system.py (update)

def get_provider_config() -> Dict[str, Any]:
    """
    Get provider configuration from environment variables or .env file.

    Returns:
        Dict[str, Any]: Provider configuration
    """
    settings = get_settings()

    config = {
        "default_provider": get_env_or_default("DEVSYNTH_PROVIDER", "openai"),
        "openai": {
            "api_key": get_env_or_default("OPENAI_API_KEY"),
            "model": get_env_or_default("OPENAI_MODEL", "gpt-4"),
            "base_url": get_env_or_default(
                "OPENAI_BASE_URL", "https://api.openai.com/v1"
            ),
        },
        "lm_studio": {
            "endpoint": get_env_or_default(
                "LM_STUDIO_ENDPOINT", "http://127.0.0.1:1234"
            ),
            "model": get_env_or_default("LM_STUDIO_MODEL", "default"),
        },
        "mcp": {  # Add MCP configuration
            "endpoint": get_env_or_default(
                "MCP_SERVER_ENDPOINT", "http://localhost:8000"
            ),
            "api_key": get_env_or_default("MCP_SERVER_API_KEY"),
            "model": get_env_or_default("MCP_SERVER_MODEL", "claude-3-opus-20240229"),
        },
        "retry": {
            "max_retries": getattr(settings, "provider_max_retries", 3),
            "initial_delay": getattr(settings, "provider_initial_delay", 1.0),
            "exponential_base": getattr(settings, "provider_exponential_base", 2.0),
            "max_delay": getattr(settings, "provider_max_delay", 60.0),
            "jitter": getattr(settings, "provider_jitter", True),
        },
        "fallback": {
            "enabled": getattr(settings, "provider_fallback_enabled", True),
            "order": getattr(settings, "provider_fallback_order", "openai,lm_studio,mcp").split(","),
        },
        "circuit_breaker": {
            "enabled": getattr(settings, "provider_circuit_breaker_enabled", True),
            "failure_threshold": getattr(settings, "provider_failure_threshold", 5),
            "recovery_timeout": getattr(settings, "provider_recovery_timeout", 60.0),
        },
    }

    # Check for .env file and load if exists
    env_path = os.path.join(os.getcwd(), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        os.environ[key] = value

                        # Update config based on loaded .env values
                        if key == "OPENAI_API_KEY":
                            config["openai"]["api_key"] = value
                        elif key == "OPENAI_MODEL":
                            config["openai"]["model"] = value
                        elif key == "LM_STUDIO_ENDPOINT":
                            config["lm_studio"]["endpoint"] = value
                        elif key == "LM_STUDIO_MODEL":
                            config["lm_studio"]["model"] = value
                        elif key == "DEVSYNTH_PROVIDER":
                            config["default_provider"] = value
                        elif key == "MCP_SERVER_ENDPOINT":  # Add MCP environment variables
                            config["mcp"]["endpoint"] = value
                        elif key == "MCP_SERVER_API_KEY":
                            config["mcp"]["api_key"] = value
                        elif key == "MCP_SERVER_MODEL":
                            config["mcp"]["model"] = value
        except Exception as e:
            logger.warning(f"Error loading .env file: {e}")

    return config
```

```python
# src/devsynth/adapters/provider_system.py (update)

class ProviderFactory:
    """Factory class for creating provider instances."""

    @staticmethod
    def create_provider(provider_type: Optional[str] = None) -> "BaseProvider":
        """
        Create a provider instance based on the specified type or config.

        Args:
            provider_type: Optional provider type, defaults to config value

        Returns:
            BaseProvider: A provider instance

        Raises:
            ProviderError: If provider creation fails
        """
        config = get_provider_config()
        tls_settings = get_settings()
        tls_conf = TLSConfig(
            verify=getattr(tls_settings, "tls_verify", True),
            cert_file=getattr(tls_settings, "tls_cert_file", None),
            key_file=getattr(tls_settings, "tls_key_file", None),
            ca_file=getattr(tls_settings, "tls_ca_file", None),
        )

        if provider_type is None:
            provider_type = config["default_provider"]

        try:
            if provider_type.lower() == ProviderType.OPENAI.value:
                if not config["openai"]["api_key"]:
                    logger.warning(
                        "OpenAI API key not found; falling back to LM Studio if available"
                    )
                    return ProviderFactory.create_provider(ProviderType.LM_STUDIO.value)
                logger.info("Using OpenAI provider")
                return OpenAIProvider(
                    api_key=config["openai"]["api_key"],
                    model=config["openai"]["model"],
                    base_url=config["openai"]["base_url"],
                    tls_config=tls_conf,
                )
            elif provider_type.lower() == ProviderType.LM_STUDIO.value:
                logger.info("Using LM Studio provider")
                return LMStudioProvider(
                    endpoint=config["lm_studio"]["endpoint"],
                    model=config["lm_studio"]["model"],
                    tls_config=tls_conf,
                )
            elif provider_type.lower() == ProviderType.MCP.value:  # Add MCP provider
                logger.info("Using MCP provider")
                return MCPProvider(
                    endpoint=config["mcp"]["endpoint"],
                    api_key=config["mcp"]["api_key"],
                    model=config["mcp"]["model"],
                    tls_config=tls_conf,
                )
            else:
                logger.warning(
                    f"Unknown provider type '{provider_type}', falling back to OpenAI"
                )
                return ProviderFactory.create_provider(ProviderType.OPENAI.value)
        except Exception as e:
            logger.error(f"Failed to create provider {provider_type}: {e}")
            raise ProviderError(f"Failed to create provider {provider_type}: {e}")
```

#### 2.3 Configuration Update

Update the configuration system to include MCP server settings:

```python
# src/devsynth/config/settings.py (update)
class Settings(BaseSettings):
    # ... existing settings ...

    # MCP Server settings
    mcp_server_endpoint: str = Field(
        default="http://localhost:8000",
        description="MCP server endpoint URL"
    )
    mcp_server_api_key: Optional[str] = Field(
        default=None,
        description="API key for MCP server authentication"
    )
    mcp_server_model: str = Field(
        default="claude-3-opus-20240229",
        description="Default model to use with MCP server"
    )
    mcp_use_sdk: bool = Field(
        default=True,
        description="Whether to use the MCP SDK (if available) or HTTP fallback"
    )
```

#### 2.4 Doctor Command Update

Update the doctor command to check MCP server connectivity:

```python
# src/devsynth/application/cli/commands/doctor_cmd.py (update)
def _check_services(bridge: UXBridge) -> bool:
    """Check if required services are available.

    Args:
        bridge: UX bridge for interaction

    Returns:
        True if all required services are available, False otherwise
    """
    # ... existing checks ...

    # Check MCP server if configured
    provider_type = os.environ.get("DEVSYNTH_PROVIDER", "").lower()
    if provider_type == "mcp":
        bridge.display_result("[blue]Checking MCP server connection...[/blue]")

        endpoint = os.environ.get("MCP_SERVER_ENDPOINT", "http://localhost:8000")
        api_key = os.environ.get("MCP_SERVER_API_KEY")

        try:
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            response = httpx.get(f"{endpoint}/health", headers=headers, timeout=5)
            response.raise_for_status()

            bridge.display_result("[green]MCP server connection successful.[/green]")
        except Exception as e:
            bridge.display_result(f"[yellow]Warning: Could not connect to MCP server: {e}[/yellow]")
            bridge.display_result("[yellow]Some features may not work correctly.[/yellow]")

            if not bridge.confirm_choice("Continue anyway?", default=False):
                return False

    return True
```

### 3. Documentation Alignment

#### 3.1 Shell Command Execution Documentation

Create documentation for the shell command execution feature:

```markdown
# Shell Command Execution

DevSynth provides the ability to execute shell commands for running test suites and other operations. This feature is particularly useful for integrating with existing test frameworks and CI/CD pipelines.

## Running Test Suites

You can run test suites using the `run-pipeline` command:

```bash
# Run all tests
devsynth run-pipeline

# Run only unit tests
devsynth run-pipeline --target unit-tests

# Run only integration tests
devsynth run-pipeline --target integration-tests

# Run only behavior tests
devsynth run-pipeline --target behavior-tests
```

## Custom Commands

You can also execute custom shell commands:

```bash
# Run a custom pytest command
devsynth run-pipeline --command "pytest tests/unit -v"

# Run a custom test command with specific options
devsynth run-pipeline --command "python -m unittest discover -s tests/unit -p 'test_*.py'"
```

## Programmatic Usage

You can use the shell command execution feature programmatically:

```python
from devsynth.adapters.shell.subprocess_adapter import SubprocessShellAdapter
from devsynth.application.testing.test_suite_runner import TestSuiteRunner

# Create shell adapter and test runner
shell_adapter = SubprocessShellAdapter()
test_runner = TestSuiteRunner(shell_adapter)

# Run pytest
result = test_runner.run_pytest("tests/unit", options=["-v"])
print(f"Tests passed: {result['tests_passed']}")

# Run custom command
result = test_runner.run_custom_command("pytest tests/unit -v")
print(f"Command output: {result['stdout']}")
```
```

#### 3.2 MCP Server Integration Documentation

Create documentation for the MCP server integration:

```markdown
# MCP Server Integration

DevSynth supports integration with MCP (Model-Context Protocol) servers, allowing you to use various LLM providers through a standardized API.

## What is MCP?

The Model-Context Protocol (MCP) is an open standard developed by Anthropic that facilitates the integration of large language models (LLMs) with external tools and data sources. This protocol aims to enhance the capabilities of LLMs by allowing them to interact with various applications and services in a standardized manner.

Key features of MCP include:
- Standardized communication between LLMs and external tools (like a "USB-C port for AI applications")
- Tool integration for performing tasks or retrieving information
- Security for data exchange between LLMs and external sources
- Client-host-server architecture for flexible deployment

## Installation

The MCP integration in DevSynth supports two modes:
1. **Native SDK Mode** (recommended): Uses the official MCP Python SDK
2. **HTTP Mode**: Direct HTTP requests as a fallback

To use the native SDK mode, install the MCP Python SDK:

```bash
pip install mcp
```

## Configuration

You can configure the MCP server integration using environment variables or the configuration system:

```bash
# Set environment variables
export DEVSYNTH_PROVIDER=mcp
export MCP_SERVER_ENDPOINT=http://localhost:8000
export MCP_SERVER_API_KEY=your-api-key
export MCP_SERVER_MODEL=claude-3-opus-20240229
export MCP_USE_SDK=true  # Set to false to force HTTP mode
```

Or using the configuration command:

```bash
# Configure MCP server
devsynth config --key provider --value mcp
devsynth config --key mcp_server_endpoint --value http://localhost:8000
devsynth config --key mcp_server_api_key --value your-api-key
devsynth config --key mcp_server_model --value claude-3-opus-20240229
devsynth config --key mcp_use_sdk --value true
```

## Usage

Once configured, DevSynth will automatically use the MCP server for all LLM operations. You can verify the connection using the doctor command:

```bash
devsynth doctor
```

## Programmatic Usage

You can use the MCP provider programmatically:

```python
from devsynth.adapters.providers.mcp_provider import MCPProvider

# Create MCP provider
provider = MCPProvider(
    endpoint="http://localhost:8000",
    api_key="your-api-key",
    model="claude-3-opus-20240229",
    use_sdk=True  # Set to False to force HTTP mode
)

# Query the provider
response = provider.complete(
    prompt="Hello, world!",
    system_prompt="You are a helpful assistant.",
    temperature=0.7,
    max_tokens=2000
)

print(f"Response: {response}")
```

## Advanced Usage with MCP SDK

If you're using the native SDK mode, you can access the underlying MCP client directly for advanced use cases:

```python
from devsynth.adapters.providers.mcp_provider import MCPProvider

# Create MCP provider
provider = MCPProvider(
    endpoint="http://localhost:8000",
    api_key="your-api-key",
    model="claude-3-opus-20240229",
    use_sdk=True
)

# Access the underlying MCP client
if hasattr(provider, 'client'):
    # Use the client directly for advanced operations
    response = provider.client.chat.completions.create(
        model=provider.model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, world!"}
        ]
    )
    print(response.choices[0].message.content)
```
```

### 4. Testing Strategy

#### 4.1 Shell Command Execution Tests

Create unit tests for the shell command execution feature:

```python
# tests/unit/adapters/shell/test_subprocess_adapter.py
import pytest
from unittest.mock import patch, MagicMock
import subprocess

from devsynth.adapters.shell.subprocess_adapter import SubprocessShellAdapter

class TestSubprocessShellAdapter:
    """Tests for the subprocess shell adapter."""

    def test_execute_command_success(self):
        """Test successful command execution."""
        adapter = SubprocessShellAdapter()

        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "test output"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            result = adapter.execute("echo test")

            assert result["success"] is True
            assert result["return_code"] == 0
            assert result["stdout"] == "test output"
            assert result["stderr"] == ""

    def test_execute_command_failure(self):
        """Test failed command execution."""
        adapter = SubprocessShellAdapter()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "test", "test output", "test error")

            result = adapter.execute("invalid_command")

            assert result["success"] is False
            assert result["return_code"] == 1
            assert result["stderr"] == "test error"

    def test_execute_command_exception(self):
        """Test exception during command execution."""
        adapter = SubprocessShellAdapter()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("test error")

            result = adapter.execute("echo test")

            assert result["success"] is False
            assert result["error"] == "test error"
```

```python
# tests/unit/application/testing/test_test_suite_runner.py
import pytest
from unittest.mock import patch, MagicMock

from devsynth.application.testing.test_suite_runner import TestSuiteRunner
from devsynth.ports.shell_command_port import ShellCommandPort

class TestTestSuiteRunner:
    """Tests for the test suite runner."""

    @pytest.fixture
    def mock_shell_command_port(self):
        """Create a mock shell command port."""
        mock_port = MagicMock(spec=ShellCommandPort)
        mock_port.execute.return_value = {
            "success": True,
            "return_code": 0,
            "stdout": "===== test session starts =====\n4 passed, 1 failed, 2 skipped\n===== test session ends =====",
            "stderr": "",
            "command": ["pytest", "tests"]
        }
        return mock_port

    def test_run_pytest(self, mock_shell_command_port):
        """Test running pytest."""
        runner = TestSuiteRunner(mock_shell_command_port)

        result = runner.run_pytest("tests")

        mock_shell_command_port.execute.assert_called_once_with(["pytest", "tests"])
        assert result["success"] is True
        assert result["tests_passed"] == 4
        assert result["tests_failed"] == 1
        assert result["tests_skipped"] == 2
        assert result["tests_total"] == 7

    def test_run_pytest_with_options(self, mock_shell_command_port):
        """Test running pytest with options."""
        runner = TestSuiteRunner(mock_shell_command_port)

        result = runner.run_pytest("tests", options=["-v", "--cov"])

        mock_shell_command_port.execute.assert_called_once_with(["pytest", "tests", "-v", "--cov"])

    def test_run_unittest(self, mock_shell_command_port):
        """Test running unittest."""
        runner = TestSuiteRunner(mock_shell_command_port)

        result = runner.run_unittest("tests")

        mock_shell_command_port.execute.assert_called_once_with(
            ["python", "-m", "unittest", "discover", "-s", "tests", "-p", "test*.py"]
        )

    def test_run_custom_command(self, mock_shell_command_port):
        """Test running a custom command."""
        runner = TestSuiteRunner(mock_shell_command_port)

        result = runner.run_custom_command("echo test")

        mock_shell_command_port.execute.assert_called_once_with("echo test")
```

#### 4.2 MCP Provider Tests

Create unit tests for the MCP provider:

```python
# tests/unit/adapters/providers/test_mcp_provider.py
import pytest
from unittest.mock import patch, MagicMock
import json

from devsynth.adapters.providers.mcp_provider import MCPProvider

class TestMCPProvider:
    """Tests for the MCP provider."""

    def test_complete_success_http(self):
        """Test successful completion using HTTP mode."""
        provider = MCPProvider(endpoint="http://test.com", use_sdk=False)

        with patch("httpx.Client") as mock_client:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": "test response"
                        }
                    }
                ]
            }

            mock_client.return_value.__enter__.return_value.post.return_value = mock_response

            response = provider.complete("test prompt", system_prompt="test system")

            assert response == "test response"

    def test_complete_success_sdk(self):
        """Test successful completion using SDK mode."""
        # Mock the MCP SDK
        with patch("devsynth.adapters.providers.mcp_provider.HAS_MCP_SDK", True):
            with patch("devsynth.adapters.providers.mcp_provider.mcp") as mock_mcp:
                # Setup mock response
                mock_message = MagicMock()
                mock_message.content = "test sdk response"

                mock_choice = MagicMock()
                mock_choice.message = mock_message

                mock_response = MagicMock()
                mock_response.choices = [mock_choice]

                # Setup mock client
                mock_completions = MagicMock()
                mock_completions.create.return_value = mock_response

                mock_chat = MagicMock()
                mock_chat.completions = mock_completions

                mock_client = MagicMock()
                mock_client.chat = mock_chat

                mock_mcp.Client.return_value = mock_client
                mock_mcp.Message = MagicMock(return_value=MagicMock())

                # Create provider with SDK mode
                provider = MCPProvider(endpoint="http://test.com", use_sdk=True)

                # Test completion
                response = provider.complete("test prompt", system_prompt="test system")

                assert response == "test sdk response"
                mock_completions.create.assert_called_once()

    def test_complete_failure_http(self):
        """Test failed completion using HTTP mode."""
        provider = MCPProvider(endpoint="http://test.com", use_sdk=False)

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.post.side_effect = Exception("test error")

            with pytest.raises(Exception) as excinfo:
                provider.complete("test prompt")

            assert "MCP server error" in str(excinfo.value)

    def test_complete_failure_sdk_with_fallback(self):
        """Test SDK failure with fallback to HTTP."""
        # Mock the MCP SDK
        with patch("devsynth.adapters.providers.mcp_provider.HAS_MCP_SDK", True):
            with patch("devsynth.adapters.providers.mcp_provider.mcp") as mock_mcp:
                # Setup mock client to raise exception
                mock_completions = MagicMock()
                mock_completions.create.side_effect = Exception("sdk error")

                mock_chat = MagicMock()
                mock_chat.completions = mock_completions

                mock_client = MagicMock()
                mock_client.chat = mock_chat

                mock_mcp.Client.return_value = mock_client

                # Setup HTTP fallback to succeed
                with patch("httpx.Client") as mock_http_client:
                    mock_response = MagicMock()
                    mock_response.raise_for_status.return_value = None
                    mock_response.json.return_value = {
                        "choices": [
                            {
                                "message": {
                                    "content": "fallback response"
                                }
                            }
                        ]
                    }

                    mock_http_client.return_value.__enter__.return_value.post.return_value = mock_response

                    # Create provider with SDK mode
                    provider = MCPProvider(endpoint="http://test.com", use_sdk=True)

                    # Test completion with fallback
                    response = provider.complete("test prompt")

                    assert response == "fallback response"
                    mock_completions.create.assert_called_once()

    def test_embed_success(self):
        """Test successful embedding."""
        provider = MCPProvider(endpoint="http://test.com")

        with patch("httpx.Client") as mock_client:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "data": [
                    {
                        "embedding": [0.1, 0.2, 0.3]
                    }
                ]
            }

            mock_client.return_value.__enter__.return_value.post.return_value = mock_response

            response = provider.embed("test text")

            assert response == [[0.1, 0.2, 0.3]]
```

#### 4.3 Behavior Tests

Create behavior tests for the new features:

```gherkin
# tests/behavior/features/shell_command_execution.feature
Feature: Shell Command Execution
  As a developer using DevSynth
  I want to execute shell commands to run test suites
  So that I can integrate with existing test frameworks

  Scenario: Run pytest with custom command
    Given I have a project with pytest tests
    When I run "devsynth run-pipeline --command 'pytest tests/unit -v'"
    Then the command should execute successfully
    And the output should contain test results

  Scenario: Run unit tests with target parameter
    Given I have a project with pytest tests
    When I run "devsynth run-pipeline --target unit-tests"
    Then the command should execute successfully
    And the output should contain unit test results
```

```gherkin
# tests/behavior/features/mcp_server_integration.feature
Feature: MCP Server Integration
  As a developer using DevSynth
  I want to use MCP servers for LLM operations
  So that I can leverage different LLM providers

  Scenario: Configure MCP server with HTTP mode
    Given I have DevSynth installed
    When I run "devsynth config --key provider --value mcp"
    And I run "devsynth config --key mcp_server_endpoint --value http://localhost:8000"
    And I run "devsynth config --key mcp_use_sdk --value false"
    Then the configuration should be updated successfully

  Scenario: Configure MCP server with SDK mode
    Given I have DevSynth installed
    And I have the MCP SDK installed
    When I run "devsynth config --key provider --value mcp"
    And I run "devsynth config --key mcp_server_endpoint --value http://localhost:8000"
    And I run "devsynth config --key mcp_use_sdk --value true"
    Then the configuration should be updated successfully

  Scenario: Check MCP server connection
    Given I have configured the MCP server
    When I run "devsynth doctor"
    Then the output should indicate MCP server status

  Scenario: Use MCP server for completions
    Given I have configured the MCP server
    When I run "devsynth generate --prompt 'Hello, world!'"
    Then the output should contain a response from the MCP server
```

## Timeline and Milestones

### Phase 1: Shell Command Execution (2 weeks)

#### Week 1: Core Implementation
- Create shell command port and adapter
- Implement test suite runner service
- Update run-pipeline command
- Write unit tests

#### Week 2: Integration and Testing
- Integrate with CLI
- Create behavior tests
- Write documentation
- Perform integration testing

### Phase 2: MCP Server Integration (2 weeks)

#### Week 1: Core Implementation
- Create MCP provider adapter with dual implementation (SDK and HTTP)
- Add MCP SDK dependency and integration
- Update provider factory
- Update configuration system
- Write unit tests

#### Week 2: Integration and Testing
- Update doctor command
- Create behavior tests
- Write documentation
- Perform integration testing
- Test both SDK and HTTP fallback modes

### Phase 3: Documentation Alignment (1 week)

- Update existing documentation to reference new features
- Create comprehensive documentation for shell command execution
- Create comprehensive documentation for MCP server integration
- Update release plan to include new features

### Phase 4: Final Testing and Release (1 week)

- Perform comprehensive testing of both features
- Address any issues or bugs
- Finalize documentation
- Prepare for release

## Conclusion

This implementation plan provides a comprehensive approach to adding shell command execution for running test suites and MCP Server integration to DevSynth. The plan follows DevSynth's hexagonal architecture and development approach, ensuring that the new features are well-integrated with the existing codebase.

The implementation includes:
- A flexible shell command execution system that can run various test suites
- A robust MCP Server integration that follows the existing provider pattern
  - Native SDK integration for optimal performance and feature support
  - HTTP fallback mode for environments without the SDK
- Comprehensive documentation for both features
- Thorough testing at unit, integration, and behavior levels

By following this plan, DevSynth will gain powerful new capabilities that enhance its flexibility and integration options. The dual-mode implementation for MCP Server integration ensures maximum compatibility and performance across different environments, while the shell command execution feature provides seamless integration with existing test frameworks and CI/CD pipelines.
