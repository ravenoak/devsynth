import pytest
from pytest_bdd import scenarios

from .steps.test_webui_navigation_prompts_steps import *  # noqa: F401,F403


pytestmark = [pytest.mark.fast]

scenarios("general/webui_navigation_prompts.feature")
