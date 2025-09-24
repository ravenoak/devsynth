"""
Defines a base agent graph structure using LangGraph.
This provides a template for creating agentic workflows with state management.
"""

# ``langgraph`` may be stubbed by tests. Import with fallback support.
try:  # pragma: no cover - import guard
    from langgraph.graph import END, StateGraph
except ImportError:  # pragma: no cover - stubbed in tests
    StateGraph = None  # type: ignore
    END = None  # type: ignore
from typing import Any, Dict, List

from devsynth.adapters.provider_system import (
    ProviderError,
)
from devsynth.adapters.provider_system import (
    complete as llm_complete,  # Renamed to avoid conflict
)
from devsynth.agents.graph_state import AgentState
from devsynth.agents.tools import get_tool_registry
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


def get_available_tools() -> List[Dict[str, Any]]:
    """Return formatted metadata for all registered tools."""
    registry = get_tool_registry()
    tools = []
    for name, meta in registry.list_tools().items():
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": meta["description"],
                    "parameters": meta["parameters"],
                },
            }
        )
    return tools


def process_input_node(state: AgentState) -> AgentState:
    """Processes the initial input request."""
    logger.info(f"Processing input: {state['input_request'][:100]}...")
    # Fetch available tools for the agent
    tools = get_available_tools()
    state_with_tools = {**state, "available_tools": tools}
    # Simple processing for now, can be expanded
    processed = state["input_request"].strip()
    if not processed:
        return {**state_with_tools, "error": "Input request cannot be empty."}
    return {**state_with_tools, "processed_input": processed}


def llm_call_node(state: AgentState) -> AgentState:
    """Makes a call to the LLM using the provider system."""
    if state.get("error"):
        return state  # Skip if there's an error

    input_prompt = state.get("processed_input")
    if not input_prompt:
        return {**state, "error": "Processed input is missing for LLM call."}

    logger.info(f"Calling LLM with prompt: {input_prompt[:100]}...")
    try:
        # System prompt could be configured or passed in state
        system_prompt = "You are a helpful AI assistant."
        tools = state.get("available_tools")
        parameters = {"tools": tools} if tools else None
        response = llm_complete(
            prompt=input_prompt,
            system_prompt=system_prompt,
            fallback=True,  # Use fallback provider
            parameters=parameters,
        )
        logger.info(f"LLM response received: {response[:100]}...")
        return {**state, "llm_response": response}
    except ProviderError as e:
        logger.error("LLM call failed: %s", e)
        return {**state, "error": f"LLM call failed: {e}"}


def parse_output_node(state: AgentState) -> AgentState:
    """Parses the LLM response into a final output."""
    if state.get("error"):
        return state  # Skip if there's an error

    llm_response = state.get("llm_response")
    if not llm_response:
        # This case might indicate an issue if llm_call_node was supposed to run
        logger.warning("LLM response is missing for parsing, passing through.")
        return {**state, "final_output": ""}  # Or handle as an error

    logger.info(f"Parsing LLM output: {llm_response[:100]}...")
    # Simple parsing for now, can be expanded
    final_output = llm_response.strip()
    return {**state, "final_output": final_output}


# Define the graph. If ``StateGraph`` is unavailable (tests may stub it with
# ``object``), fall back to a minimal sequential implementation so imports
# succeed during behavior tests.
if callable(StateGraph) and StateGraph is not object:
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("process_input", process_input_node)
    workflow.add_node("llm_call", llm_call_node)
    workflow.add_node("parse_output", parse_output_node)

    # Define edges
    workflow.set_entry_point("process_input")
    workflow.add_edge("process_input", "llm_call")
    workflow.add_edge("llm_call", "parse_output")
    workflow.add_edge("parse_output", END)

    # Compile the graph
    base_agent_graph = workflow.compile()
else:  # pragma: no cover - simple fallback used in stubbed test envs

    class _FallbackGraph:
        def invoke(self, state: AgentState) -> AgentState:
            state = process_input_node(state)
            state = llm_call_node(state)
            state = parse_output_node(state)
            return state

    base_agent_graph = _FallbackGraph()

# Example usage (for testing or demonstration)
if __name__ == "__main__":
    initial_state = {
        "input_request": (
            "Explain the benefits of using LangGraph for agent development."
        ),
        # Other fields will be populated by the graph
        "processed_input": None,
        "llm_response": None,
        "intermediate_steps": None,
        "final_output": None,
        "error": None,
    }

    # Ensure OPENAI_API_KEY or LM_STUDIO_ENDPOINT is set in your environment
    # or .env file for this example to work.
    try:
        final_state = base_agent_graph.invoke(initial_state)
        logger.info("--- Final State ---")
        for key, value in final_state.items():
            logger.info(
                "%s: %s%s",
                key,
                str(value)[:500],
                "..." if len(str(value)) > 500 else "",
            )
    except ProviderError as e:
        logger.exception("Error invoking graph: %s", e)
        logger.error(
            "Please ensure your LLM provider (OpenAI or LM Studio) "
            "is configured correctly."
        )
