"""
Test file for EDRR integration with real LLM providers.
"""

import os

import pytest
from pytest_bdd import scenarios

# Mark all scenarios with documented resource markers for live providers

pytestmark = [
    pytest.mark.fast,
    pytest.mark.requires_resource("openai"),
    pytest.mark.requires_resource("lmstudio"),
]

# Import the step definitions
from tests.behavior.steps.test_edrr_real_llm_integration_steps import *  # noqa: F401,F403

# Get the absolute path to the feature file
feature_file = os.path.join(
    os.path.dirname(__file__),
    "features",
    "general",
    "edrr_real_llm_integration.feature",
)

# Import the scenarios from the feature file
scenarios(feature_file)
