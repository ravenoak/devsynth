"""
Unit tests for the LangGraph agent system components.
"""
import pytest
from unittest.mock import patch, MagicMock

from devsynth.agents.graph_state import AgentState
from devsynth.agents.base_agent_graph import (
    process_input_node,
    llm_call_node,
    parse_output_node,
    base_agent_graph # To test compilation
)
from devsynth.adapters.provider_system import ProviderError

# Test AgentState (it's a TypedDict, so mostly for type checking, but can ensure keys)
def test_agent_state_keys():
    """Test that AgentState can be created and has expected keys."""
    state = AgentState(
        input_request="test",
        processed_input=None,
        llm_response=None,
        intermediate_steps=None,
        final_output=None,
        error=None
    )
    assert "input_request" in state
    assert state["input_request"] == "test"

# Test process_input_node
def test_process_input_node_success():
    """Test process_input_node with valid input."""
    initial_state = AgentState(input_request="  hello world  ", processed_input=None, llm_response=None, intermediate_steps=None, final_output=None, error=None)
    updated_state = process_input_node(initial_state)
    assert updated_state["processed_input"] == "hello world"
    assert updated_state.get("error") is None

def test_process_input_node_empty_input():
    """Test process_input_node with empty input."""
    initial_state = AgentState(input_request="", processed_input=None, llm_response=None, intermediate_steps=None, final_output=None, error=None)
    updated_state = process_input_node(initial_state)
    assert "Input request cannot be empty" in updated_state.get("error", "")
    assert updated_state.get("processed_input") is None

# Test llm_call_node
@patch("devsynth.agents.base_agent_graph.llm_complete")
def test_llm_call_node_success(mock_llm_complete):
    """Test llm_call_node with successful LLM call."""
    mock_llm_complete.return_value = "LLM says hello"
    initial_state = AgentState(input_request="test", processed_input="test prompt", llm_response=None, intermediate_steps=None, final_output=None, error=None)
    updated_state = llm_call_node(initial_state)

    mock_llm_complete.assert_called_once_with(
        prompt="test prompt",
        system_prompt="You are a helpful AI assistant.",
        fallback=True
    )
    assert updated_state["llm_response"] == "LLM says hello"
    assert updated_state.get("error") is None

@patch("devsynth.agents.base_agent_graph.llm_complete")
def test_llm_call_node_llm_failure(mock_llm_complete):
    """Test llm_call_node when LLM call fails."""
    mock_llm_complete.side_effect = ProviderError("LLM unavailable")
    initial_state = AgentState(input_request="test", processed_input="test prompt", llm_response=None, intermediate_steps=None, final_output=None, error=None)
    updated_state = llm_call_node(initial_state)

    assert "LLM call failed: LLM unavailable" in updated_state.get("error", "")
    assert updated_state.get("llm_response") is None

def test_llm_call_node_skip_on_prior_error():
    """Test llm_call_node skips if there's a prior error in state."""
    initial_state = AgentState(input_request="test", processed_input="test prompt", llm_response=None, intermediate_steps=None, final_output=None, error="Previous error")
    updated_state = llm_call_node(initial_state)
    assert updated_state["error"] == "Previous error" # Error should be preserved
    assert updated_state.get("llm_response") is None

def test_llm_call_node_missing_processed_input():
    """Test llm_call_node if processed_input is missing."""
    initial_state = AgentState(input_request="test", processed_input=None, llm_response=None, intermediate_steps=None, final_output=None, error=None)
    updated_state = llm_call_node(initial_state)
    assert "Processed input is missing for LLM call" in updated_state.get("error", "")
    assert updated_state.get("llm_response") is None

# Test parse_output_node
def test_parse_output_node_success():
    """Test parse_output_node with valid LLM response."""
    initial_state = AgentState(input_request="test", processed_input="test", llm_response="  parsed output  ", intermediate_steps=None, final_output=None, error=None)
    updated_state = parse_output_node(initial_state)
    assert updated_state["final_output"] == "parsed output"
    assert updated_state.get("error") is None

def test_parse_output_node_missing_llm_response():
    """Test parse_output_node if llm_response is missing."""
    initial_state = AgentState(input_request="test", processed_input="test", llm_response=None, intermediate_steps=None, final_output=None, error=None)
    updated_state = parse_output_node(initial_state)
    # Depending on strictness, this might be an error or just empty output
    assert updated_state["final_output"] == ""
    # assert "LLM response is missing for parsing" in updated_state.get("error", "") # If strict

def test_parse_output_node_skip_on_prior_error():
    """Test parse_output_node skips if there's a prior error in state."""
    initial_state = AgentState(input_request="test", processed_input="test", llm_response="response", intermediate_steps=None, final_output=None, error="Previous error")
    updated_state = parse_output_node(initial_state)
    assert updated_state["error"] == "Previous error"
    assert updated_state.get("final_output") is None

# Test graph compilation (simple check)
def test_base_agent_graph_compiles():
    """Test that the base_agent_graph compiles without errors."""
    assert base_agent_graph is not None
    assert hasattr(base_agent_graph, 'invoke'), "Compiled graph should have an invoke method"

