# API Reference

This document is now located at technical_reference/api_reference/index.md

This document provides detailed information about the internal APIs and extension interfaces of DevSynth.

## Table of Contents

- [Domain Interfaces](#domain-interfaces)
- [Application APIs](#application-apis)
- [Adapter Interfaces](#adapter-interfaces)
- [Port Definitions](#port-definitions)
- [Extension APIs](#extension-apis)

## Domain Interfaces

The domain interfaces define the core contracts that must be implemented by various components of the system.

### Agent Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class AgentInterface(ABC):
    """Interface for agent implementations."""
    
    @abstractmethod
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task and return the result.
        
        Args:
            task: A dictionary containing task information
            
        Returns:
            A dictionary containing the task result
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get the capabilities of this agent.
        
        Returns:
            A dictionary of capability names and descriptions
        """
        pass
```

### Memory Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class MemoryInterface(ABC):
    """Interface for memory storage implementations."""
    
    @abstractmethod
    def add(self, item: Dict[str, Any]) -> str:
        """
        Add an item to memory.
        
        Args:
            item: The item to add
            
        Returns:
            The ID of the added item
        """
        pass
    
    @abstractmethod
    def get(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an item from memory.
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            The item if found, None otherwise
        """
        pass
    
    @abstractmethod
    def update(self, item_id: str, item: Dict[str, Any]) -> bool:
        """
        Update an item in memory.
        
        Args:
            item_id: The ID of the item to update
            item: The updated item
            
        Returns:
            True if the update was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, item_id: str) -> bool:
        """
        Delete an item from memory.
        
        Args:
            item_id: The ID of the item to delete
            
        Returns:
            True if the deletion was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def query(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query items in memory.
        
        Args:
            query: Query parameters
            
        Returns:
            A list of items matching the query
        """
        pass
```

### LLM Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class LLMInterface(ABC):
    """Interface for LLM provider implementations."""
    
    @abstractmethod
    def query(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Query the LLM with a prompt.
        
        Args:
            prompt: The prompt to send to the LLM
            **kwargs: Additional parameters for the query
            
        Returns:
            A dictionary containing the LLM response
        """
        pass
    
    @abstractmethod
    def get_token_count(self, text: str) -> int:
        """
        Get the token count for a text.
        
        Args:
            text: The text to count tokens for
            
        Returns:
            The number of tokens in the text
        """
        pass
```

### Orchestrator Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable

class OrchestratorInterface(ABC):
    """Interface for workflow orchestration implementations."""
    
    @abstractmethod
    def register_step(self, name: str, handler: Callable) -> None:
        """
        Register a step in the workflow.
        
        Args:
            name: The name of the step
            handler: The function to handle the step
        """
        pass
    
    @abstractmethod
    def execute_workflow(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the workflow.
        
        Args:
            initial_state: The initial state for the workflow
            
        Returns:
            The final state after workflow execution
        """
        pass
```

## Application APIs

The application layer provides implementations of the domain interfaces and defines the core functionality of DevSynth.

### Base Agent

```python
from devsynth.domain.interfaces.agent import AgentInterface
from devsynth.domain.interfaces.llm import LLMInterface
from devsynth.domain.interfaces.memory import MemoryInterface
from typing import Dict, Any, Optional, List

class BaseAgent(AgentInterface):
    """Base class for agent implementations."""
    
    def __init__(self, llm: LLMInterface, memory: MemoryInterface):
        """
        Initialize the agent.
        
        Args:
            llm: The LLM provider
            memory: The memory provider
        """
        self.llm = llm
        self.memory = memory
        
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task and return the result.
        
        Args:
            task: A dictionary containing task information
            
        Returns:
            A dictionary containing the task result
        """
        # Implementation details
        
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get the capabilities of this agent.
        
        Returns:
            A dictionary of capability names and descriptions
        """
        # Implementation details
```

### Context Manager

```python
from devsynth.domain.interfaces.memory import MemoryInterface
from typing import Dict, Any, Optional, List

class ContextManager:
    """Manages context information for agents."""
    
    def __init__(self, memory: MemoryInterface):
        """
        Initialize the context manager.
        
        Args:
            memory: The memory provider
        """
        self.memory = memory
        
    def add_context(self, context_type: str, data: Dict[str, Any]) -> str:
        """
        Add context information.
        
        Args:
            context_type: The type of context (task, memory, runtime, social)
            data: The context data
            
        Returns:
            The ID of the added context
        """
        # Implementation details
        
    def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """
        Get context information.
        
        Args:
            context_id: The ID of the context to retrieve
            
        Returns:
            The context if found, None otherwise
        """
        # Implementation details
        
    def update_context(self, context_id: str, data: Dict[str, Any]) -> bool:
        """
        Update context information.
        
        Args:
            context_id: The ID of the context to update
            data: The updated context data
            
        Returns:
            True if the update was successful, False otherwise
        """
        # Implementation details
        
    def delete_context(self, context_id: str) -> bool:
        """
        Delete context information.
        
        Args:
            context_id: The ID of the context to delete
            
        Returns:
            True if the deletion was successful, False otherwise
        """
        # Implementation details
        
    def query_context(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query context information.
        
        Args:
            query: Query parameters
            
        Returns:
            A list of contexts matching the query
        """
        # Implementation details
        
    def prune_context(self, max_tokens: int) -> int:
        """
        Prune context to stay within token limits.
        
        Args:
            max_tokens: The maximum number of tokens to keep
            
        Returns:
            The number of tokens removed
        """
        # Implementation details
```

### Workflow

```python
from devsynth.domain.interfaces.orchestrator import OrchestratorInterface
from typing import Dict, Any, Optional, List, Callable

class Workflow:
    """Implements the development workflow."""
    
    def __init__(self, orchestrator: OrchestratorInterface):
        """
        Initialize the workflow.
        
        Args:
            orchestrator: The workflow orchestrator
        """
        self.orchestrator = orchestrator
        self._register_steps()
        
    def _register_steps(self) -> None:
        """Register workflow steps with the orchestrator."""
        # Implementation details
        
    def execute(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the workflow.
        
        Args:
            initial_state: The initial state for the workflow
            
        Returns:
            The final state after workflow execution
        """
        return self.orchestrator.execute_workflow(initial_state)
```

## Adapter Interfaces

The adapter interfaces define how DevSynth interacts with external systems.

### CLI Adapter

```python
from devsynth.domain.interfaces.cli import CLIInterface
from typing import Dict, Any, Optional, List

class CLIAdapter(CLIInterface):
    """Adapter for command-line interface."""
    
    def register_commands(self) -> None:
        """Register CLI commands."""
        # Implementation details
        
    def run(self) -> None:
        """Run the CLI application."""
        # Implementation details
```

### LLM Adapter

```python
from devsynth.domain.interfaces.llm import LLMInterface
from typing import Dict, Any, Optional, List

class LLMAdapter:
    """Adapter for LLM providers."""
    
    def __init__(self, provider: LLMInterface):
        """
        Initialize the adapter.
        
        Args:
            provider: The LLM provider
        """
        self.provider = provider
        
    def query(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Query the LLM with a prompt.
        
        Args:
            prompt: The prompt to send to the LLM
            **kwargs: Additional parameters for the query
            
        Returns:
            A dictionary containing the LLM response
        """
        return self.provider.query(prompt, **kwargs)
        
    def get_token_count(self, text: str) -> int:
        """
        Get the token count for a text.
        
        Args:
            text: The text to count tokens for
            
        Returns:
            The number of tokens in the text
        """
        return self.provider.get_token_count(text)
```

## Port Definitions

The port definitions provide the interfaces between the application and adapters.

### Agent Port

```python
from devsynth.domain.interfaces.agent import AgentInterface
from typing import Dict, Any, Optional, List

class AgentPort:
    """Port for agent functionality."""
    
    def __init__(self, agent: AgentInterface):
        """
        Initialize the port.
        
        Args:
            agent: The agent implementation
        """
        self.agent = agent
        
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task and return the result.
        
        Args:
            task: A dictionary containing task information
            
        Returns:
            A dictionary containing the task result
        """
        return self.agent.execute_task(task)
        
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get the capabilities of this agent.
        
        Returns:
            A dictionary of capability names and descriptions
        """
        return self.agent.get_capabilities()
```

### Memory Port

```python
from devsynth.domain.interfaces.memory import MemoryInterface
from typing import Dict, Any, Optional, List

class MemoryPort:
    """Port for memory functionality."""
    
    def __init__(self, memory: MemoryInterface):
        """
        Initialize the port.
        
        Args:
            memory: The memory implementation
        """
        self.memory = memory
        
    def add(self, item: Dict[str, Any]) -> str:
        """
        Add an item to memory.
        
        Args:
            item: The item to add
            
        Returns:
            The ID of the added item
        """
        return self.memory.add(item)
        
    def get(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an item from memory.
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            The item if found, None otherwise
        """
        return self.memory.get(item_id)
        
    def update(self, item_id: str, item: Dict[str, Any]) -> bool:
        """
        Update an item in memory.
        
        Args:
            item_id: The ID of the item to update
            item: The updated item
            
        Returns:
            True if the update was successful, False otherwise
        """
        return self.memory.update(item_id, item)
        
    def delete(self, item_id: str) -> bool:
        """
        Delete an item from memory.
        
        Args:
            item_id: The ID of the item to delete
            
        Returns:
            True if the deletion was successful, False otherwise
        """
        return self.memory.delete(item_id)
        
    def query(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query items in memory.
        
        Args:
            query: Query parameters
            
        Returns:
            A list of items matching the query
        """
        return self.memory.query(query)
```

## Extension APIs

The extension APIs provide mechanisms for extending DevSynth with custom functionality.

### Creating a Custom Agent

To create a custom agent, extend the `BaseAgent` class and implement the required methods:

```python
from devsynth.application.agents.base import BaseAgent
from devsynth.domain.interfaces.llm import LLMInterface
from devsynth.domain.interfaces.memory import MemoryInterface
from typing import Dict, Any

class CustomAgent(BaseAgent):
    """A custom agent implementation."""
    
    def __init__(self, llm: LLMInterface, memory: MemoryInterface):
        """
        Initialize the agent.
        
        Args:
            llm: The LLM provider
            memory: The memory provider
        """
        super().__init__(llm, memory)
        
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task and return the result.
        
        Args:
            task: A dictionary containing task information
            
        Returns:
            A dictionary containing the task result
        """
        # Custom implementation
        task_type = task.get("type", "unknown")
        
        if task_type == "custom_task":
            # Handle custom task
            result = self._handle_custom_task(task)
        else:
            # Delegate to parent implementation
            result = super().execute_task(task)
            
        return result
        
    def _handle_custom_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a custom task.
        
        Args:
            task: The task to handle
            
        Returns:
            The task result
        """
        # Custom task handling logic
        return {"status": "success", "result": "Custom task completed"}
        
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get the capabilities of this agent.
        
        Returns:
            A dictionary of capability names and descriptions
        """
        capabilities = super().get_capabilities()
        capabilities.update({
            "custom_task": "Handles custom tasks specific to this agent"
        })
        return capabilities
```

### Creating a Custom LLM Provider

To create a custom LLM provider, implement the `LLMInterface`:

```python
from devsynth.domain.interfaces.llm import LLMInterface
from typing import Dict, Any
import requests

class CustomLLMProvider(LLMInterface):
    """A custom LLM provider implementation."""
    
    def __init__(self, api_key: str, endpoint: str):
        """
        Initialize the provider.
        
        Args:
            api_key: API key for the LLM service
            endpoint: API endpoint for the LLM service
        """
        self.api_key = api_key
        self.endpoint = endpoint
        
    def query(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Query the LLM with a prompt.
        
        Args:
            prompt: The prompt to send to the LLM
            **kwargs: Additional parameters for the query
            
        Returns:
            A dictionary containing the LLM response
        """
        # Custom implementation for querying the LLM
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "prompt": prompt,
            "max_tokens": kwargs.get("max_tokens", 1000),
            "temperature": kwargs.get("temperature", 0.7)
        }
        
        response = requests.post(self.endpoint, headers=headers, json=data)
        response.raise_for_status()
        
        return response.json()
        
    def get_token_count(self, text: str) -> int:
        """
        Get the token count for a text.
        
        Args:
            text: The text to count tokens for
            
        Returns:
            The number of tokens in the text
        """
        # Simple approximation (replace with actual tokenization logic)
        return len(text.split()) * 1.3
```

### Adding a Custom CLI Command

To add a custom CLI command, use the command registry from the CLI adapter:

```python
from devsynth.adapters.cli.typer_adapter import cli
import typer

@cli.command()
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

