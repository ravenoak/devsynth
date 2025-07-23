from pytest_bdd import scenarios

from .steps.webui_onboarding_steps import *  # noqa: F401,F403

# Load scenarios from the feature file using the pytest-bdd base directory
scenarios("general/webui_onboarding_flow.feature")
