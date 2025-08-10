from pytest_bdd import scenarios

from .steps.test_webui_commands_steps import *  # noqa: F401,F403
from .steps.webui_steps import *  # noqa: F401,F403

scenarios("general/webui_commands.feature")
