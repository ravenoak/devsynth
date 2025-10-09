"""Test file for EDRR integration with real LLM providers."""

import pytest
from pytest_bdd import scenarios

# Mark all scenarios with documented resource markers for live providers

pytestmark = [
    pytest.mark.fast,
    pytest.mark.requires_resource("openai"),
    pytest.mark.requires_resource("lmstudio"),
]

from tests.behavior.feature_paths import feature_path

# Import the step definitions
from tests.behavior.steps.test_edrr_real_llm_integration_steps import *  # noqa: F401,F403

# Import the scenarios from the canonical behavior asset path.
scenarios(feature_path(__file__, "general", "edrr_real_llm_integration.feature"))
