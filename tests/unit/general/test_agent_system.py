"""
Unit tests for the LangGraph agent system components.
"""

from unittest.mock import MagicMock, patch

import pytest

from devsynth.adapters.provider_system import ProviderError
from devsynth.agents.base_agent_graph import (
    base_agent_graph,
    get_available_tools,
    llm_call_node,
    parse_output_node,
    process_input_node,
)
from devsynth.agents.graph_state import AgentState


def test_agent_state_keys_has_expected():
    """Test that AgentState can be created and has expected keys.

    ReqID: N/A"""
    state = AgentState(
        input_request="test",
        processed_input=None,
        llm_response=None,
        intermediate_steps=None,
        final_output=None,
        error=None,
    )
    assert "input_request" in state
    assert state["input_request"] == "test"


def test_process_input_node_success_is_valid():
    """Test process_input_node with valid input.

    ReqID: N/A"""
    initial_state = AgentState(
        input_request="  hello world  ",
        processed_input=None,
        llm_response=None,
        intermediate_steps=None,
        final_output=None,
        error=None,
    )
    updated_state = process_input_node(initial_state)
    assert updated_state["processed_input"] == "hello world"
    assert updated_state.get("error") is None


def test_process_input_node_empty_input_succeeds():
    """Test process_input_node with empty input.

    ReqID: N/A"""
    initial_state = AgentState(
        input_request="",
        processed_input=None,
        llm_response=None,
        intermediate_steps=None,
        final_output=None,
        error=None,
    )
    updated_state = process_input_node(initial_state)
    assert "Input request cannot be empty" in updated_state.get("error", "")
    assert updated_state.get("processed_input") is None


def test_process_input_node_adds_tool_list():
    """Process node should add available tools to state."""
    initial_state = AgentState(
        input_request="tools test",
        processed_input=None,
        llm_response=None,
        intermediate_steps=None,
        final_output=None,
        error=None,
    )
    updated_state = process_input_node(initial_state)
    assert updated_state.get("available_tools") == get_available_tools()


@patch("devsynth.agents.base_agent_graph.llm_complete")
def test_llm_call_node_success_succeeds(mock_llm_complete):
    """Test llm_call_node with successful LLM call.

    ReqID: N/A"""
    mock_llm_complete.return_value = "LLM says hello"
    state = process_input_node(
        AgentState(
            input_request="test prompt",
            processed_input=None,
            llm_response=None,
            intermediate_steps=None,
            final_output=None,
            error=None,
        )
    )
    updated_state = llm_call_node(state)
    expected_tools = state["available_tools"]
    mock_llm_complete.assert_called_once_with(
        prompt="test prompt",
        system_prompt="You are a helpful AI assistant.",
        fallback=True,
        parameters={"tools": expected_tools},
    )
    assert updated_state["llm_response"] == "LLM says hello"
    assert updated_state.get("error") is None


@patch("devsynth.agents.base_agent_graph.llm_complete")
def test_llm_call_node_llm_failure_fails(mock_llm_complete):
    """Test llm_call_node when LLM call fails.

    ReqID: N/A"""
    mock_llm_complete.side_effect = ProviderError("LLM unavailable")
    state = process_input_node(
        AgentState(
            input_request="test prompt",
            processed_input=None,
            llm_response=None,
            intermediate_steps=None,
            final_output=None,
            error=None,
        )
    )
    updated_state = llm_call_node(state)
    expected_tools = state["available_tools"]
    mock_llm_complete.assert_called_once_with(
        prompt="test prompt",
        system_prompt="You are a helpful AI assistant.",
        fallback=True,
        parameters={"tools": expected_tools},
    )
    assert "LLM call failed: LLM unavailable" in updated_state.get("error", "")
    assert updated_state.get("llm_response") is None


def test_llm_call_node_skip_on_prior_error_raises_error():
    """Test llm_call_node skips if there's a prior error in state.

    ReqID: N/A"""
    initial_state = AgentState(
        input_request="test",
        processed_input="test prompt",
        llm_response=None,
        intermediate_steps=None,
        final_output=None,
        error="Previous error",
    )
    updated_state = llm_call_node(initial_state)
    assert updated_state["error"] == "Previous error"
    assert updated_state.get("llm_response") is None


def test_llm_call_node_missing_processed_input_succeeds():
    """Test llm_call_node if processed_input is missing.

    ReqID: N/A"""
    initial_state = AgentState(
        input_request="test",
        processed_input=None,
        llm_response=None,
        intermediate_steps=None,
        final_output=None,
        error=None,
        available_tools=get_available_tools(),
    )
    updated_state = llm_call_node(initial_state)
    assert "Processed input is missing for LLM call" in updated_state.get("error", "")
    assert updated_state.get("llm_response") is None


def test_parse_output_node_success_is_valid():
    """Test parse_output_node with valid LLM response.

    ReqID: N/A"""
    initial_state = AgentState(
        input_request="test",
        processed_input="test",
        llm_response="  parsed output  ",
        intermediate_steps=None,
        final_output=None,
        error=None,
    )
    updated_state = parse_output_node(initial_state)
    assert updated_state["final_output"] == "parsed output"
    assert updated_state.get("error") is None


def test_parse_output_node_missing_llm_response_succeeds():
    """Test parse_output_node if llm_response is missing.

    ReqID: N/A"""
    initial_state = AgentState(
        input_request="test",
        processed_input="test",
        llm_response=None,
        intermediate_steps=None,
        final_output=None,
        error=None,
    )
    updated_state = parse_output_node(initial_state)
    assert updated_state["final_output"] == ""


def test_parse_output_node_skip_on_prior_error_raises_error():
    """Test parse_output_node skips if there's a prior error in state.

    ReqID: N/A"""
    initial_state = AgentState(
        input_request="test",
        processed_input="test",
        llm_response="response",
        intermediate_steps=None,
        final_output=None,
        error="Previous error",
    )
    updated_state = parse_output_node(initial_state)
    assert updated_state["error"] == "Previous error"
    assert updated_state.get("final_output") is None


def test_base_agent_graph_compiles_raises_error():
    """Test that the base_agent_graph compiles without errors.

    ReqID: N/A"""
    assert base_agent_graph is not None
    assert hasattr(
        base_agent_graph, "invoke"
    ), "Compiled graph should have an invoke method"
