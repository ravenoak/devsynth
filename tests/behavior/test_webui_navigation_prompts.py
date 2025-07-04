from pytest_bdd import scenarios

from .steps.webui_navigation_prompts_steps import *  # noqa: F401,F403

scenarios("webui_navigation_prompts.feature")
