"""Focused coverage tests for domain/models/agent.py missing lines."""

import pytest

from devsynth.domain.models.agent import AgentConfig, AgentType


@pytest.mark.fast
def test_agent_config_post_init_with_none_values():
    """Test AgentConfig.__post_init__ when capabilities and parameters are None."""
    # This tests lines 54-57 which are currently missing coverage
    config = AgentConfig(
        name="TestAgent",
        agent_type=AgentType.EXPERT,
        capabilities=None,
        parameters=None,
    )

    # __post_init__ should initialize empty lists/dicts
    assert config.capabilities == []
    assert config.parameters == {}


@pytest.mark.fast
def test_agent_config_post_init_with_existing_values():
    """Test AgentConfig.__post_init__ when capabilities and parameters are already set."""
    existing_caps = ["test_capability"]
    existing_params = {"test": "value"}

    config = AgentConfig(
        name="TestAgent", capabilities=existing_caps, parameters=existing_params
    )

    # Should not overwrite existing values
    assert config.capabilities is existing_caps
    assert config.parameters is existing_params
