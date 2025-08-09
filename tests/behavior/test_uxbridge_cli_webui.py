from pytest_bdd import scenarios

from .steps.test_uxbridge_shared_steps import *  # noqa: F401,F403

scenarios("general/uxbridge_cli_webui.feature")
