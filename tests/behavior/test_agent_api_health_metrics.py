"""BDD scenarios for Agent API health and metrics endpoints."""

import pytest
from pytest_bdd import scenarios

from tests.behavior.feature_paths import feature_path

from .steps.test_agent_api_health_metrics_steps import *  # noqa: F401,F403


pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "agent_api_health_metrics.feature"))
