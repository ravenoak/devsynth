from pytest_bdd import scenarios

from .steps.webui_onboarding_steps import *  # noqa: F401,F403

scenarios("features/webui_onboarding_flow.feature")
