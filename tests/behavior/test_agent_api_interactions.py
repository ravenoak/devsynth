from pytest_bdd import scenarios

from .steps.agent_api_steps import *  # noqa: F401,F403

scenarios("features/agent_api_interactions.feature")
