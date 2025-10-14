"""
Core orchestration step executor.

This module centralizes business rules for executing a workflow step so that
adapters (e.g., LangGraph adapter) remain thin and focused on integration.

Aligned with project guidelines and docs/plan.md (architecture boundaries).
"""

from __future__ import annotations

from typing import Any, Dict

# Keep imports adapter-agnostic. We rely on duck typing for `state` and `step`.
from devsynth.adapters.agents.agent_adapter import AgentAdapter
from devsynth.application.llm.providers import SimpleLLMProviderFactory
from devsynth.ports.llm_port import LLMPort


class OrchestrationService:
    """Encapsulates business rules for processing workflow steps.

    Notes:
    - This keeps adapters thin by removing LLM provider setup, agent/team
      construction, and task shaping from adapter glue code.
    - The service accepts `state` and `step` as dynamic objects to avoid
      circular dependencies with adapter-local types. They must provide the
      attributes used below (duck typing).
    """

    def __init__(self) -> None:
        # In the future, this can accept configuration or factories via DI.
        self._llm_factory = SimpleLLMProviderFactory()

    def process_step(
        self, state: Any, step: Any
    ) -> Any:  # pragma: no cover - thin wrapper
        """Process a single workflow step and update the given state.

        Expected attributes:
        - state.workflow_id, state.context, state.messages, state.project_root
        - step.id, step.name, step.description, step.agent_type
        """
        # Configure a default provider (LM Studio local) for local/offline-friendly usage.
        # This mirrors the previous adapter behavior.
        self._llm_factory.create_provider(
            "lmstudio",
            {
                "api_base": "http://localhost:1234",
                "model": "local_model",
                "max_tokens": 2048,
            },
        )

        llm_port = LLMPort(self._llm_factory)
        llm_port.set_default_provider(
            "lmstudio",
            {
                "api_base": "http://localhost:1234",
                "model": "local_model",
                "max_tokens": 2048,
            },
        )

        agent_adapter = AgentAdapter(llm_port)

        # Team construction (WSDE model): currently include multiple agent types.
        team_id = f"{state.workflow_id}_{step.id}"
        agent_adapter.create_team(team_id)

        agent_types = [
            "planner",
            "specification",
            "test",
            "code",
            "validation",
            "refactor",
            "documentation",
            "diagram",
            "critic",
        ]
        for agent_type in agent_types:
            agent = agent_adapter.create_agent(
                agent_type,
                {
                    "name": f"{agent_type}_agent",
                    "description": f"Agent for {agent_type} tasks",
                    "capabilities": [],
                },
            )
            agent_adapter.add_agent_to_team(agent)

        # Log step execution context into messages
        state.messages.append(
            {
                "role": "system",
                "content": (
                    f"Executing step: {step.name} - {step.description} "
                    f"with agent type: {step.agent_type}"
                ),
            }
        )

        task: dict[str, Any] = {
            "step_id": step.id,
            "step_name": step.name,
            "step_description": step.description,
            "context": state.context,
            "messages": state.messages,
            "project_root": getattr(state, "project_root", ""),
            "task_type": step.agent_type,
        }

        result = agent_adapter.process_task(task)

        # Update the state with the result message
        state.messages.append({"role": "agent", "content": f"Agent result: {result}"})

        # Human-in-the-loop signaling
        if isinstance(result, dict) and result.get("needs_human", False):
            state.needs_human = True
            state.human_message = result.get(
                "human_message", f"Human input needed for step {step.name}"
            )

        return state
