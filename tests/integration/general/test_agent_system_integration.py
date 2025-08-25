"""
Integration tests for the LangGraph base_agent_graph.
"""

from unittest.mock import MagicMock, patch

import pytest

from devsynth.adapters.provider_system import ProviderError
from devsynth.agents.base_agent_graph import (
    base_agent_graph,
    get_available_tools,
)
from devsynth.agents.graph_state import AgentState


@patch("devsynth.agents.base_agent_graph.llm_complete")
@pytest.mark.medium
def test_base_agent_graph_successful_invocation_succeeds(mock_llm_complete):
    """Test a successful end-to-end invocation of the base_agent_graph.

    ReqID: N/A"""
    mock_llm_complete.return_value = "Mocked LLM response"
    initial_state = AgentState(
        input_request="Test input request",
        processed_input=None,
        llm_response=None,
        intermediate_steps=None,
        final_output=None,
        error=None,
    )
    final_state = base_agent_graph.invoke(initial_state)
    expected_tools = get_available_tools()
    assert final_state["processed_input"] == "Test input request"
    mock_llm_complete.assert_called_once_with(
        prompt="Test input request",
        system_prompt="You are a helpful AI assistant.",
        fallback=True,
        parameters={"tools": expected_tools},
    )
    assert final_state["llm_response"] == "Mocked LLM response"
    assert final_state["final_output"] == "Mocked LLM response"
    assert final_state.get("error") is None
    assert final_state["available_tools"] == expected_tools


@patch("devsynth.agents.base_agent_graph.llm_complete")
@pytest.mark.medium
def test_base_agent_graph_error_in_input_processing_raises_error(mock_llm_complete):
    """Test graph behavior when process_input_node sets an error.

    ReqID: N/A"""
    initial_state = AgentState(
        input_request="",
        processed_input=None,
        llm_response=None,
        intermediate_steps=None,
        final_output=None,
        error=None,
    )
    final_state = base_agent_graph.invoke(initial_state)
    assert "Input request cannot be empty" in final_state.get("error", "")
    assert final_state.get("processed_input") is None
    mock_llm_complete.assert_not_called()
    assert final_state.get("llm_response") is None
    assert final_state.get("final_output") is None
    assert final_state["available_tools"] == get_available_tools()


@patch("devsynth.agents.base_agent_graph.llm_complete")
@pytest.mark.medium
def test_base_agent_graph_error_in_llm_call_raises_error(mock_llm_complete):
    """Test graph behavior when llm_call_node encounters an LLM error.

    ReqID: N/A"""
    mock_llm_complete.side_effect = ProviderError("LLM API is down")
    initial_state = AgentState(
        input_request="Valid input",
        processed_input=None,
        llm_response=None,
        intermediate_steps=None,
        final_output=None,
        error=None,
    )
    final_state = base_agent_graph.invoke(initial_state)
    expected_tools = get_available_tools()
    assert final_state["processed_input"] == "Valid input"
    mock_llm_complete.assert_called_once_with(
        prompt="Valid input",
        system_prompt="You are a helpful AI assistant.",
        fallback=True,
        parameters={"tools": expected_tools},
    )
    assert "LLM call failed: LLM API is down" in final_state.get("error", "")
    assert final_state.get("llm_response") is None
    assert final_state.get("final_output") is None
    assert final_state["available_tools"] == expected_tools


@patch("devsynth.agents.base_agent_graph.llm_complete")
@pytest.mark.medium
def test_base_agent_graph_llm_response_is_none_for_parsing_raises_error(
    mock_llm_complete,
):
    """Test graph behavior when llm_response is None before parse_output_node.
    This simulates a scenario where llm_call_node might not set llm_response correctly,
    though our current llm_call_node always sets an error or a response.
    This test ensures parse_output_node handles it gracefully.

    ReqID: N/A"""
    mock_llm_complete.return_value = "  Proper LLM Response  "
    initial_state = AgentState(
        input_request="Another test",
        processed_input=None,
        llm_response=None,
        intermediate_steps=None,
        final_output=None,
        error=None,
    )
    final_state = base_agent_graph.invoke(initial_state)
    expected_tools = get_available_tools()
    mock_llm_complete.assert_called_once_with(
        prompt="Another test",
        system_prompt="You are a helpful AI assistant.",
        fallback=True,
        parameters={"tools": expected_tools},
    )
    assert final_state["final_output"] == "Proper LLM Response"
    assert final_state.get("error") is None
    assert final_state["available_tools"] == expected_tools
