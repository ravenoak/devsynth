from tests.behavior.feature_paths import feature_path
import pytest
from pytest_bdd import scenarios

from .steps.test_agent_api_steps import *  # noqa: F401,F403


pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "agent_api_interactions.feature"))
