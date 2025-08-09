from pytest_bdd import scenarios

from .steps.test_webui_navigation_prompts_steps import *  # noqa: F401,F403

scenarios("general/webui_navigation_prompts.feature")
