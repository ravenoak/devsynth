from pytest_bdd import scenarios

from .steps.test_agent_api_steps import *  # noqa: F401,F403

scenarios("general/agent_api_interactions.feature")
