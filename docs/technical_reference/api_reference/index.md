---

author: DevSynth Team
date: '2025-07-07'
last_reviewed: "2025-07-10"
status: published
tags:

- technical-reference

title: API Reference
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="../index.md">Technical Reference</a> &gt; <a href="index.md">Api Reference</a> &gt; API Reference
</div>

# API Reference

This document provides detailed information about the internal APIs and extension interfaces of DevSynth.

## Table of Contents

- [Domain Interfaces](#domain-interfaces)
- [Application APIs](#application-apis)
- [Adapter Interfaces](#adapter-interfaces)
- [Port Definitions](#port-definitions)
- [Extension APIs](#extension-apis)


## Domain Interfaces

The domain interfaces define the core contracts that must be implemented by various components of the system.

### Agent Interfaces

```python
from typing import Any, Dict, List, Optional, Protocol
from ...domain.models.agent import AgentConfig

class Agent(Protocol):
    """Protocol for agents in the DevSynth system."""

    def initialize(self, config: AgentConfig) -> None:
        """Initialize the agent with configuration."""
        ...

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task and return the result."""
        ...

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the capabilities of this agent."""
        ...

class AgentFactory(Protocol):
    """Protocol for creating agents."""

    def create_agent(self, agent_type: str, config: Dict[str, Any] = None) -> Agent:
        """Create an agent of the specified type."""
        ...

    def register_agent_type(self, agent_type: str, agent_class: type) -> None:
        """Register a new agent type."""
        ...

class AgentCoordinator(Protocol):
    """Protocol for coordinating multiple agents."""

    def add_agent(self, agent: Agent) -> None:
        """Add an agent to the coordinator."""
        ...

    def delegate_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate a task to the appropriate agent(s)."""
        ...
```

### Memory Interfaces

```python
from typing import Any, Dict, List, Optional, Protocol
from ...domain.models.memory import MemoryItem, MemoryType, MemoryVector

class MemoryStore(Protocol):
    """Protocol for memory storage."""

    def store(self, item: MemoryItem) -> str:
        """Store an item in memory and return its ID."""
        ...

    def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve an item from memory by ID."""
        ...

    def search(self, query: Dict[str, Any]) -> List[MemoryItem]:
        """Search for items in memory matching the query."""
        ...

    def delete(self, item_id: str) -> bool:
        """Delete an item from memory."""
        ...

class VectorStore(Protocol):
    """Protocol for vector storage."""

    def store_vector(self, vector: MemoryVector) -> str:
        """Store a vector in the vector store and return its ID."""
        ...

    def retrieve_vector(self, vector_id: str) -> Optional[MemoryVector]:
        """Retrieve a vector from the vector store by ID."""
        ...

    def similarity_search(
        self, query_embedding: List[float], top_k: int = 5
    ) -> List[MemoryVector]:
        """Search for vectors similar to the query embedding."""
        ...

    def delete_vector(self, vector_id: str) -> bool:
        """Delete a vector from the vector store."""
        ...

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection."""
        ...

class ContextManager(Protocol):
    """Protocol for managing context."""

    def add_to_context(self, key: str, value: Any) -> None:
        """Add a value to the current context."""
        ...

    def get_from_context(self, key: str) -> Optional[Any]:
        """Get a value from the current context."""
        ...

    def get_full_context(self) -> Dict[str, Any]:
        """Get the full current context."""
        ...

    def clear_context(self) -> None:
        """Clear the current context."""
        ...

class VectorStoreProviderFactory(Protocol):
    """Protocol for creating VectorStore providers."""

    def create_provider(
        self, provider_type: str, config: Dict[str, Any] | None = None
    ) -> VectorStore:
        """Create a VectorStore provider of the specified type."""
        ...

    def register_provider_type(self, provider_type: str, provider_class: type) -> None:
        """Register a new provider type."""
        ...
```

### LLM Interfaces

```python
from typing import Any, Dict, List, Optional, Protocol, AsyncGenerator

class LLMProvider(Protocol):
    """Protocol for LLM providers."""

    def generate(self, prompt: str, parameters: Dict[str, Any] = None) -> str:
        """Generate text from a prompt."""
        ...

    def generate_with_context(self, prompt: str, context: List[Dict[str, str]], parameters: Dict[str, Any] = None) -> str:
        """Generate text from a prompt with conversation context."""
        ...

    def get_embedding(self, text: str) -> List[float]:
        """Get an embedding vector for the given text."""
        ...

class StreamingLLMProvider(LLMProvider, Protocol):
    """Protocol for LLM providers that support streaming."""

    async def generate_stream(self, prompt: str, parameters: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        """Generate text from a prompt with streaming."""
        ...

    async def generate_with_context_stream(self, prompt: str, context: List[Dict[str, str]], parameters: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        """Generate text from a prompt with conversation context with streaming."""
        ...

class LLMProviderFactory(Protocol):
    """Protocol for creating LLM providers."""

    def create_provider(self, provider_type: str, config: Dict[str, Any] = None) -> LLMProvider:
        """Create an Provider of the specified type."""
        ...

    def register_provider_type(self, provider_type: str, provider_class: type) -> None:
        """Register a new provider type."""
        ...
```

## Application APIs

The application layer provides implementations of the domain interfaces and defines the core functionality of DevSynth.

### Base Agent

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from ...domain.interfaces.agent import Agent
from ...domain.models.agent import AgentConfig
from ...domain.models.WSDE import WSDE
from ...ports.llm_port import LLMPort

class BaseAgent(Agent, ABC):
    """Base class for all agents in the DevSynth system."""

    def __init__(self):
        self.config = None
        self.current_role = None  # Current WSDE role (Worker, Supervisor, Designer, Evaluator, Primus)
        self.llm_port = None

    def initialize(self, config: AgentConfig) -> None:
        """Initialize the agent with configuration."""
        self.config = config

    def set_llm_port(self, llm_port: LLMPort) -> None:
        """Set the LLM port for this agent."""
        self.llm_port = llm_port

    def generate_text(self, prompt: str, parameters: Dict[str, Any] = None) -> str:
        """Generate text using the LLM port."""
        if self.llm_port is None:
            return f"Placeholder text for prompt: {prompt[:30]}..."

        try:
            return self.llm_port.generate(prompt, parameters)
        except Exception as e:
            return f"Error generating text: {str(e)}"

    def generate_text_with_context(self, prompt: str, context: List[Dict[str, str]], parameters: Dict[str, Any] = None) -> str:
        """Generate text with conversation context using the LLM port."""
        if self.llm_port is None:
            return f"Placeholder text for prompt with context: {prompt[:30]}..."

        try:
            return self.llm_port.generate_with_context(prompt, context, parameters)
        except Exception as e:
            return f"Error generating text with context: {str(e)}"

    @abstractmethod
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs and produce outputs."""
        pass

    def get_capabilities(self) -> List[str]:
        """Get the capabilities of this agent."""
        if self.config:
            return self.config.capabilities
        return []

    @property
    def name(self) -> str:
        """Get the name of this agent."""
        if self.config:
            return self.config.name
        return self.__class__.__name__

    @property
    def agent_type(self) -> str:
        """Get the type of this agent."""
        if self.config:
            return self.config.agent_type.value
        return "base"

    @property
    def description(self) -> str:
        """Get the description of this agent."""
        if self.config:
            return self.config.description
        return "Base agent"

    def create_wsde(self, content: str, content_type: str = "text", metadata: Dict[str, Any] = None) -> WSDE:
        """Create a new WSDE with the given content."""
        return WSDE(
            content=content,
            content_type=content_type,
            metadata=metadata or {}
        )

    def update_wsde(self, WSDE: WSDE, content: str = None, metadata: Dict[str, Any] = None) -> WSDE:
        """Update an existing WSDE."""
        if content is not None:
            WSDE.content = content

        if metadata:
            WSDE.metadata.update(metadata)

        return WSDE

    def get_role_prompt(self) -> str:
        """Get a prompt based on the current WSDE role."""
        if self.current_role == "Worker":
            return "As the Worker, your job is to perform the actual work and implement the solution."
        elif self.current_role == "Supervisor":
            return "As the Supervisor, your job is to oversee the work and provide guidance and direction."
        elif self.current_role == "Designer":
            return "As the Designer, your job is to plan and design the approach and architecture."
        elif self.current_role == "Evaluator":
            return "As the Evaluator, your job is to evaluate the output and provide feedback for improvement."
        elif self.current_role == "Primus":
            return "As the Primus, you are the lead for this task. Coordinate the team and make final decisions."
        else:
            return ""
```

### Context Managers

```python
from typing import Any, Dict, List, Optional
from ...domain.interfaces.memory import ContextManager

class SimpleContextManager(ContextManager):
    """Simple in-memory implementation of the ContextManager protocol."""

    def __init__(self):
        self._context = {}

    def add_to_context(self, key: str, value: Any) -> None:
        """Add a value to the current context."""
        self._context[key] = value

    def get_from_context(self, key: str) -> Optional[Any]:
        """Get a value from the current context."""
        return self._context.get(key)

    def get_full_context(self) -> Dict[str, Any]:
        """Get the full current context."""
        return self._context.copy()

    def clear_context(self) -> None:
        """Clear the current context."""
        self._context.clear()

class PersistentContextManager(ContextManager):
    """Persistent implementation of the ContextManager protocol using a memory store."""

    def __init__(self, memory_store):
        self._memory_store = memory_store
        self._context_id = "current_context"
        self._ensure_context_exists()

    def _ensure_context_exists(self) -> None:
        """Ensure the context exists in the memory store."""
        context = self._memory_store.retrieve(self._context_id)
        if context is None:
            from ...domain.models.memory import MemoryItem, MemoryType
            context_item = MemoryItem(
                id=self._context_id,
                content={},
                memory_type=MemoryType.SHORT_TERM,
                metadata={"type": "context"}
            )
            self._memory_store.store(context_item)

    def add_to_context(self, key: str, value: Any) -> None:
        """Add a value to the current context."""
        context = self._memory_store.retrieve(self._context_id)
        if context:
            context.content[key] = value
            self._memory_store.store(context)

    def get_from_context(self, key: str) -> Optional[Any]:
        """Get a value from the current context."""
        context = self._memory_store.retrieve(self._context_id)
        if context:
            return context.content.get(key)
        return None

    def get_full_context(self) -> Dict[str, Any]:
        """Get the full current context."""
        context = self._memory_store.retrieve(self._context_id)
        if context:
            return context.content.copy()
        return {}

    def clear_context(self) -> None:
        """Clear the current context."""
        context = self._memory_store.retrieve(self._context_id)
        if context:
            context.content = {}
            self._memory_store.store(context)
```

### Workflow Management

```python
from typing import Dict, Any, Optional, List, Callable
from uuid import uuid4
from ...domain.models.workflow import Workflow, WorkflowStep, WorkflowStatus
from ...ports.orchestration_port import OrchestrationPort
from ...adapters.orchestration.langgraph_adapter import (
    LangGraphWorkflowEngine,
    FileSystemWorkflowRepository,
    NeedsHumanInterventionError,
)
from devsynth.interface.ux_bridge import UXBridge

class WorkflowManager:
    """Manages workflows for the DevSynth system."""

    def __init__(self, bridge: UXBridge):
        """Initialize the workflow manager."""
        self.bridge = bridge
        # Set up human intervention callback
        self.orchestration_port = OrchestrationPort(
            workflow_engine=LangGraphWorkflowEngine(
                human_intervention_callback=self._handle_human_intervention
            ),
            workflow_repository=FileSystemWorkflowRepository(),
        )

    def _handle_human_intervention(
        self, workflow_id: str, step_id: str, message: str
    ) -> str:
        """Handle human intervention requests."""
        self.bridge.display_result("[yellow]Human intervention required:[/yellow]")
        self.bridge.display_result(f"[bold]{message}[/bold]")
        response = self.bridge.ask_question("Your input")
        return response

    def _create_workflow_for_command(
        self, command: str, args: Dict[str, Any]
    ) -> Workflow:
        """Create a workflow for a specific command."""
        workflow = self.orchestration_port.create_workflow(
            name=f"{command}-workflow-{uuid4().hex[:8]}",
            description=f"Workflow for {command} command",
        )

        # Add steps based on the command
        if command == "init":
            self._add_init_workflow_steps(workflow, args)
        elif command == "inspect":
            self._add_inspect_workflow_steps(workflow, args)
        elif command == "spec":
            self._add_spec_workflow_steps(workflow, args)
        elif command == "test":
            self._add_test_workflow_steps(workflow, args)
        elif command == "code":
            self._add_code_workflow_steps(workflow, args)
        elif command == "run":
            self._add_run_workflow_steps(workflow, args)
        elif command == "config":
            self._add_config_workflow_steps(workflow, args)

        return workflow

    def execute_command(self, command: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command through the workflow system."""
        try:
            # Create context with command and arguments
            context = {
                "command": command,
                "project_root": args.get("path", None),
                **args,
            }

            # Create workflow for the command
            workflow = self._create_workflow_for_command(command, args)

            # Execute the workflow
            try:
                executed_workflow = self.orchestration_port.execute_workflow(
                    workflow_id=workflow.id, context=context
                )

                # Return result based on workflow status
                if executed_workflow.status == WorkflowStatus.COMPLETED:
                    return {
                        "success": True,
                        "message": "Command executed successfully",
                        "workflow_id": workflow.id,
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Command status: {executed_workflow.status.value}",
                        "workflow_id": workflow.id,
                    }

            except NeedsHumanInterventionError as e:
                # Handle human intervention
                user_input = self._handle_human_intervention(
                    e.workflow_id, e.step_id, e.message
                )

                # Try executing the workflow again with the human input
                executed_workflow = self.orchestration_port.execute_workflow(
                    workflow_id=workflow.id,
                    context={**context, "human_input": user_input},
                )

                return {
                    "success": True,
                    "message": "Command executed successfully after human intervention",
                    "workflow_id": workflow.id,
                }

        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the status of a workflow."""
        return self.orchestration_port.get_workflow_status(workflow_id)
```

## Adapter Interfaces

The adapter interfaces define how DevSynth interacts with external systems.

### CLI Adapter

```python
import typer
from typing import Optional
from devsynth.application.cli import (
    init_cmd,
    spec_cmd,
    test_cmd,
    code_cmd,
    run_pipeline_cmd,
    config_cmd,
    # ... other commands
)

def build_app() -> typer.Typer:
    """Create a Typer application with all commands registered."""
    app = typer.Typer(
        help=(
            "DevSynth CLI - automate iterative 'Expand, Differentiate, Refine, "
            "Retrace' workflows."
        ),
    )

    # Register commands from the application layer
    app.command(
        name="init",
        help=("Initialize or onboard a project. Use --wizard for interactive setup."),
    )(init_cmd)
    app.command(
        name="spec",
        help="Generate specifications from requirements. Example: devsynth spec --requirements-file reqs.md",
    )(spec_cmd)
    # ... other commands

    @app.callback(invoke_without_command=True)
    def main(ctx: typer.Context):
        if ctx.invoked_subcommand is None:
            typer.echo(ctx.get_help())
            raise typer.Exit()

    return app

# Provide a default app instance for convenience

app = build_app()

def run_cli() -> None:
    """Entry point for the Typer application."""
    build_app()()
```

## LLM Adapters

```python
from typing import Any, Dict, List, Optional
from ...domain.interfaces.llm import LLMProvider, LLMProviderFactory
from ...application.llm.providers import SimpleLLMProviderFactory

class LLMBackendAdapter:
    """Adapter for LLM backends."""

    def __init__(self):
        self.factory = SimpleLLMProviderFactory()

    def create_provider(self, provider_type: str, config: Dict[str, Any] = None) -> LLMProvider:
        """Create an Provider of the specified type."""
        return self.factory.create_provider(provider_type, config)

    def register_provider_type(self, provider_type: str, provider_class: type) -> None:
        """Register a new provider type."""
        self.factory.register_provider_type(provider_type, provider_class)
```

### Chat Adapters

```python
from typing import Any, Dict, List, Optional, Callable
from rich.console import Console
from rich.prompt import Prompt
from ...ports.chat_port import ChatPort

class CLIChatAdapter(ChatPort):
    """CLI implementation of the chat port."""

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize the CLI chat adapter.

        Args:
            console: Rich console for output (optional)
        """
        self.console = console or Console()

    def display_message(self, message: str, sender: str = "System", style: str = None) -> None:
        """
        Display a chat message in the CLI.

        Args:
            message: The message to display
            sender: The sender of the message
            style: Rich style to apply to the message
        """
        style = style or "bold green" if sender == "System" else "bold blue"
        self.console.print(f"[{style}]{sender}:[/{style}] {message}")

    def run_chat_session(self, handler: Callable[[str], str], initial_message: str = None) -> None:
        """
        Run an interactive chat session in the CLI.

        Args:
            handler: Function to handle user input and return responses
            initial_message: Optional initial message to display
        """
        if initial_message:
            self.display_message(initial_message)

        while True:
            user_input = Prompt.ask("[bold]You[/bold]")

            if user_input.lower() in ("exit", "quit", "bye"):
                self.display_message("Goodbye!", "System")
                break

            response = handler(user_input)
            self.display_message(response, "Assistant", "bold green")
```

## Port Definitions

The port definitions provide the interfaces between the application and adapters.

### Agent Port

```python
from typing import Any, Dict, List, Optional
from ..domain.interfaces.agent import Agent, AgentFactory, AgentCoordinator
from ..domain.models.agent import AgentConfig

class AgentPort:
    """Port for the agent system."""

    def __init__(self, agent_factory: AgentFactory, agent_coordinator: AgentCoordinator):
        self.agent_factory = agent_factory
        self.agent_coordinator = agent_coordinator

    def create_agent(self, agent_type: str, config: Dict[str, Any] = None) -> Agent:
        """Create an agent of the specified type."""
        agent = self.agent_factory.create_agent(agent_type, config)
        self.agent_coordinator.add_agent(agent)
        return agent

    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task using the appropriate agent(s)."""
        return self.agent_coordinator.delegate_task(task)

    def register_agent_type(self, agent_type: str, agent_class: type) -> None:
        """Register a new agent type."""
        self.agent_factory.register_agent_type(agent_type, agent_class)
```

### Memory Port

```python
from typing import Any, Dict, List, Optional
from ..domain.interfaces.memory import MemoryStore, ContextManager
from ..domain.models.memory import MemoryItem, MemoryType
from devsynth.metrics import inc_memory

class MemoryPort:
    """Port for the memory and context system, using Kuzu as the default backend."""

    def __init__(
        self,
        context_manager: ContextManager,
        memory_store: Optional[MemoryStore] = None,
    ):
        # Use KuzuMemoryStore by default, but allow override for testing/extensibility
        if memory_store is None:
            # Lazy import to avoid circular dependency
            from devsynth.adapters.kuzu_memory_store import KuzuMemoryStore

            memory_store = KuzuMemoryStore()
        self.memory_store = memory_store
        self.context_manager = context_manager

    def store_memory(
        self, content: Any, memory_type: MemoryType, metadata: Dict[str, Any] = None
    ) -> str:
        """Store an item in memory and return its ID."""
        item = MemoryItem(
            id="", content=content, memory_type=memory_type, metadata=metadata
        )
        inc_memory("store")
        return self.memory_store.store(item)

    def retrieve_memory(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve an item from memory by ID."""
        inc_memory("retrieve")
        return self.memory_store.retrieve(item_id)

    def search_memory(self, query: Dict[str, Any]) -> List[MemoryItem]:
        """Search for items in memory matching the query."""
        inc_memory("search")
        return self.memory_store.search(query)

    def add_to_context(self, key: str, value: Any) -> None:
        """Add a value to the current context."""
        inc_memory("add_context")
        self.context_manager.add_to_context(key, value)

    def get_from_context(self, key: str) -> Optional[Any]:
        """Get a value from the current context."""
        inc_memory("get_context")
        return self.context_manager.get_from_context(key)

    def get_full_context(self) -> Dict[str, Any]:
        """Get the full current context."""
        inc_memory("get_full_context")
        return self.context_manager.get_full_context()
```

### LLM Port

```python
from typing import Any, Dict, List, Optional
from ..domain.interfaces.llm import LLMProvider

class LLMPort:
    """Port for LLM functionality."""

    def __init__(self, provider: LLMProvider):
        self.provider = provider

    def generate(self, prompt: str, parameters: Dict[str, Any] = None) -> str:
        """Generate text from a prompt."""
        return self.provider.generate(prompt, parameters)

    def generate_with_context(self, prompt: str, context: List[Dict[str, str]], parameters: Dict[str, Any] = None) -> str:
        """Generate text from a prompt with conversation context."""
        return self.provider.generate_with_context(prompt, context, parameters)

    def get_embedding(self, text: str) -> List[float]:
        """Get an embedding vector for the given text."""
        return self.provider.get_embedding(text)
```

### Orchestration Port

```python
from typing import Any, Dict, Optional
from ..domain.models.workflow import Workflow, WorkflowStep

class OrchestrationPort:
    """Port for workflow orchestration."""

    def __init__(self, workflow_engine, workflow_repository):
        self.workflow_engine = workflow_engine
        self.workflow_repository = workflow_repository

    def create_workflow(self, name: str, description: str) -> Workflow:
        """Create a new workflow."""
        return self.workflow_repository.create_workflow(name, description)

    def add_step(self, workflow: Workflow, step: WorkflowStep) -> None:
        """Add a step to a workflow."""
        self.workflow_repository.add_step(workflow, step)

    def execute_workflow(self, workflow_id: str, context: Dict[str, Any]) -> Optional[Workflow]:
        """Execute a workflow with the given context."""
        workflow = self.workflow_repository.get_workflow(workflow_id)
        if workflow is None:
            return None

        executed_workflow = self.workflow_engine.execute(workflow, context)
        self.workflow_repository.update_workflow(executed_workflow)
        return executed_workflow

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the status of a workflow."""
        workflow = self.workflow_repository.get_workflow(workflow_id)
        if workflow is None:
            return {"status": "not_found"}

        return {
            "id": workflow.id,
            "name": workflow.name,
            "status": workflow.status.value,
            "steps": [
                {
                    "id": step.id,
                    "name": step.name,
                    "status": step.status.value,
                }
                for step in workflow.steps
            ],
        }
```

## Extension APIs

The extension APIs provide mechanisms for extending DevSynth with custom functionality.

### Creating a Custom Agent

To create a custom agent, extend the `BaseAgent` class and implement the required methods:

```python
from typing import Any, Dict, List, Optional
from devsynth.application.agents.base import BaseAgent
from devsynth.domain.models.agent import AgentConfig

class CustomAgent(BaseAgent):
    """A custom agent implementation."""

    def __init__(self):
        """Initialize the agent."""
        super().__init__()
        # Add any custom initialization here

    def initialize(self, config: AgentConfig) -> None:
        """Initialize the agent with configuration."""
        super().initialize(config)
        # Add any custom configuration handling here

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process inputs and produce outputs.

        Args:
            inputs: A dictionary containing input information

        Returns:
            A dictionary containing the processing results
        """
        # Custom implementation
        task_type = inputs.get("type", "unknown")

        if task_type == "custom_task":
            # Handle custom task
            result = self._handle_custom_task(inputs)
        else:
            # Generate a response using the LLM
            prompt = self._create_prompt(inputs)
            response = self.generate_text(prompt)
            result = {"status": "success", "result": response}

        return result

    def _handle_custom_task(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a custom task.

        Args:
            inputs: The task inputs

        Returns:
            The task result
        """
        # Custom task handling logic
        return {"status": "success", "result": "Custom task completed"}

    def _create_prompt(self, inputs: Dict[str, Any]) -> str:
        """
        Create a prompt for the LLM based on inputs.

        Args:
            inputs: The task inputs

        Returns:
            A prompt string
        """
        # Add role-based prompting if a role is assigned
        role_prompt = self.get_role_prompt()
        task_description = inputs.get("description", "")

        return f"{role_prompt}\n\nTask: {task_description}\n\nResponse:"
```

### Creating a Custom Provider

To create a custom Provider, extend the `BaseLLMProvider` class:

```python
from typing import Any, Dict, List, Optional
import httpx
from devsynth.application.llm.providers import BaseLLMProvider
from devsynth.exceptions import DevSynthError

class CustomProviderError(DevSynthError):
    """Exception raised when there's an issue with the custom provider."""
    pass

class CustomLLMProvider(BaseLLMProvider):
    """A custom Provider implementation."""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the provider.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)

        # Extract configuration
        self.api_key = self.config.get("api_key")
        self.model = self.config.get("model", "default-model")
        self.max_tokens = self.config.get("max_tokens", 1024)
        self.temperature = self.config.get("temperature", 0.7)
        self.api_base = self.config.get("api_base", "https://api.example.com")
        self.timeout = self.config.get("timeout", 60)

        if not self.api_key:
            raise CustomProviderError("API key is required")

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def generate(self, prompt: str, parameters: Dict[str, Any] = None) -> str:
        """
        Generate text from a prompt.

        Args:
            prompt: The prompt to send to the LLM
            parameters: Additional parameters for the query

        Returns:
            The generated text
        """
        params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        if parameters:
            params.update(parameters)

        payload = {
            "prompt": prompt,
            **params
        }

        try:
            response = httpx.post(
                f"{self.api_base}/v1/completions",
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            if "text" in data:
                return data["text"]
            elif "choices" in data and data["choices"]:
                return data["choices"][0]["text"]
            else:
                raise CustomProviderError("Invalid response format")

        except httpx.HTTPStatusError as e:
            raise CustomProviderError(f"API error: {e.response.text}")
        except httpx.RequestError as e:
            raise CustomProviderError(f"Connection error: {str(e)}")

    def generate_with_context(self, prompt: str, context: List[Dict[str, str]], parameters: Dict[str, Any] = None) -> str:
        """
        Generate text from a prompt with conversation context.

        Args:
            prompt: The prompt to send to the LLM
            context: List of previous messages in the conversation
            parameters: Additional parameters for the query

        Returns:
            The generated text
        """
        # Format the context and prompt into a conversation format
        messages = context.copy()
        messages.append({"role": "user", "content": prompt})

        params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        if parameters:
            params.update(parameters)

        payload = {
            "messages": messages,
            **params
        }

        try:
            response = httpx.post(
                f"{self.api_base}/v1/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            if "choices" in data and data["choices"]:
                return data["choices"][0]["message"]["content"]
            else:
                raise CustomProviderError("Invalid response format")

        except httpx.HTTPStatusError as e:
            raise CustomProviderError(f"API error: {e.response.text}")
        except httpx.RequestError as e:
            raise CustomProviderError(f"Connection error: {str(e)}")

    def get_embedding(self, text: str) -> List[float]:
        """
        Get an embedding vector for the given text.

        Args:
            text: The text to get an embedding for

        Returns:
            A list of floats representing the embedding vector
        """
        payload = {
            "input": text,
            "model": self.config.get("embedding_model", "text-embedding-ada-002")
        }

        try:
            response = httpx.post(
                f"{self.api_base}/v1/embeddings",
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            if "data" in data and data["data"]:
                return data["data"][0]["embedding"]
            else:
                raise CustomProviderError("Invalid embedding response format")

        except httpx.HTTPStatusError as e:
            raise CustomProviderError(f"API error: {e.response.text}")
        except httpx.RequestError as e:
            raise CustomProviderError(f"Connection error: {str(e)}")
```

### Registering a Custom Provider

To register your custom Provider with the factory:

```python
from devsynth.application.llm.providers import factory
from your_module import CustomLLMProvider

# Register the provider

factory.register_provider_type("custom", CustomLLMProvider)

# Now you can create instances of your provider

custom_provider = factory.create_provider("custom", {
    "api_key": "your-api-key",
    "api_base": "https://api.example.com"
})
```

## Adding a Custom CLI Command

To add a custom CLI command, use the Typer app from the CLI adapter:

```python
from devsynth.adapters.cli.typer_adapter import app
import typer

@app.command(
    name="custom-command",
    help="A custom command that does something useful"
)
def custom_command(
    param: str = typer.Option(..., help="Parameter description"),
    flag: bool = typer.Option(False, help="Flag description")
):
    """Custom command documentation."""
    if flag:
        typer.echo(f"Running custom command with parameter: {param} and flag enabled")
    else:
        typer.echo(f"Running custom command with parameter: {param}")

    # Command implementation
    result = do_something_with(param)
    typer.echo(f"Result: {result}")
```

## Conclusion

This API reference provides detailed information about the internal APIs and extension interfaces of DevSynth. By understanding these interfaces, you can extend DevSynth with custom functionality to meet your specific needs.

For more information about the architecture and design principles, refer to the [Architecture Documentation](architecture_documentation.md).
## Implementation Status

.
