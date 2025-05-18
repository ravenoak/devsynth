"""
Defines the state for LangGraph agent workflows.
"""
from typing import TypedDict, Optional, List

class AgentState(TypedDict):
    """
    Represents the state of an agent workflow.

    Attributes:
        input_request: The initial request to the agent.
        processed_input: The request after initial processing.
        llm_response: The raw response from the LLM.
        intermediate_steps: A list of intermediate steps or tool outputs (optional).
        final_output: The final formatted response from the agent.
        error: Any error message encountered during the workflow (optional).
    """
    input_request: str
    processed_input: Optional[str]
    llm_response: Optional[str]
    intermediate_steps: Optional[List[str]]
    final_output: Optional[str]
    error: Optional[str]

