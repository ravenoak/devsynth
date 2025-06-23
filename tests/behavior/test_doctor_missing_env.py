from pytest_bdd import scenarios

from .steps.cli_commands_steps import *  # noqa: F401,F403
from .steps.doctor_missing_env_steps import *  # noqa: F401,F403

scenarios("features/doctor_missing_env.feature")
