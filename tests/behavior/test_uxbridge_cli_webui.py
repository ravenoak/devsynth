from pytest_bdd import scenarios

from .steps.uxbridge_shared_steps import *  # noqa: F401,F403

scenarios("uxbridge_cli_webui.feature")
