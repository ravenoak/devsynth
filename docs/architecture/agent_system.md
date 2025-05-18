# DevSynth Agent System Architecture

## Overview

The DevSynth agent system leverages LangGraph to create modular, stateful, and resilient AI agents. This architecture allows for the construction of complex workflows where agents can perform tasks, make decisions, and interact with other DevSynth components like the memory system and provider system.

This document outlines the foundational components of the agent system, including the `AgentState` and the `base_agent_graph`.

## Core Concepts

- **LangGraph**: A library for building stateful, multi-actor applications with LLMs. It allows defining agentic workflows as graphs where nodes represent actions or computations and edges represent the flow of control.
- **AgentState**: A `TypedDict` that defines the structure of the data passed between nodes in a LangGraph. It maintains the current context and results of the agent's operations.
- **Nodes**: Functions that perform specific tasks within the agent workflow (e.g., processing input, calling an LLM, parsing output).
- **Edges**: Define the sequence of operations, connecting nodes to form a directed graph.

## AgentState (`graph_state.py`)

The `AgentState` is crucial for managing the information flow within an agent. It typically includes:

```python
from typing import TypedDict, Optional, List

class AgentState(TypedDict):
    input_request: str
    processed_input: Optional[str]
    llm_response: Optional[str]
    intermediate_steps: Optional[List[str]] # For tools or multi-step reasoning
    final_output: Optional[str]
    error: Optional[str]
```

- `input_request`: The initial query or task given to the agent.
- `processed_input`: The input after any initial cleaning or transformation.
- `llm_response`: The raw output from an LLM call.
- `intermediate_steps`: A list to store outputs from tools or intermediate reasoning steps, useful for complex agents.
- `final_output`: The agent's final answer or result after all processing.
- `error`: A field to capture any errors that occur during the workflow, allowing for graceful error handling.

## Base Agent Graph (`base_agent_graph.py`)

A foundational `base_agent_graph` provides a template for simple request-response agent workflows. It demonstrates the core pattern of input processing, LLM interaction, and output parsing.

### Workflow Diagram

```mermaid
graph TD
    A[Start] --> B(process_input_node)
    B --> C(llm_call_node)
    C --> D(parse_output_node)
    D --> E[End]
```

### Key Nodes in `base_agent_graph`:

1.  **`process_input_node`**: 
    *   Takes the `input_request` from the `AgentState`.
    *   Performs basic processing (e.g., stripping whitespace).
    *   Updates the `processed_input` field in the state.
    *   Can set an error if input is invalid.

2.  **`llm_call_node`**: 
    *   Uses the `processed_input` as the prompt for an LLM.
    *   Leverages the DevSynth `provider_system` (`devsynth.adapters.provider_system.complete`) to make the LLM call. This ensures that the agent can use either OpenAI or LM Studio, with automatic fallback.
    *   Stores the LLM's raw response in the `llm_response` field.
    *   Handles potential errors during the LLM call.

3.  **`parse_output_node`**: 
    *   Takes the `llm_response`.
    *   Performs basic parsing (e.g., stripping whitespace) to produce the final output.
    *   Stores the result in the `final_output` field.

### Graph Definition:

The graph is defined using `langgraph.graph.StateGraph` and compiled:

```python
# Simplified from base_agent_graph.py
from langgraph.graph import StateGraph, END
# ... import nodes and AgentState ...

workflow = StateGraph(AgentState)

workflow.add_node("process_input", process_input_node)
workflow.add_node("llm_call", llm_call_node)
workflow.add_node("parse_output", parse_output_node)

workflow.set_entry_point("process_input")
workflow.add_edge("process_input", "llm_call")
workflow.add_edge("llm_call", "parse_output")
workflow.add_edge("parse_output", END)

base_agent_graph = workflow.compile()
```

## Integration with Provider System

The agent system is tightly integrated with the `provider_system`. The `llm_call_node` in `base_agent_graph.py` directly uses the `complete` function from the provider system. This ensures:
-   Access to configured LLM providers (OpenAI, LM Studio).
-   Automatic fallback between providers if one is unavailable.
-   Consistent LLM interaction logic across different agents.

## Extensibility

This base agent architecture is designed for extensibility:

-   **Specialized Agents**: New agents for specific tasks (e.g., code generation, requirement analysis, self-analysis) can be created by:
    *   Defining new nodes for specialized logic.
    *   Adding new fields to `AgentState` if required.
    *   Constructing new graphs or extending the base graph with conditional edges and more complex flows.
-   **Tool Usage**: The `intermediate_steps` field in `AgentState` is a placeholder for integrating tools. Future agents can use LangGraph's built-in support for tool calling nodes.
-   **Checkpointing**: LangGraph supports checkpointing, allowing the state of long-running agents to be saved and resumed. This is a planned enhancement for DevSynth.

## Error Handling

The `AgentState` includes an `error` field. Nodes in the graph can populate this field if an issue occurs. Subsequent nodes can check this field to decide whether to proceed, attempt recovery, or terminate the workflow gracefully.

## Future Enhancements (as per Comprehensive Plan)

-   Development of specialized agent workflows (code generation, analysis, dialectic reasoning).
-   Implementation of state management and checkpointing for long-running operations.
-   Integration with NetworkX for code analysis agents.
-   Self-analysis and tuning capabilities driven by agents.

---

_Last updated: May 17, 2025_
