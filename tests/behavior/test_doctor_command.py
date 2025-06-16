from pytest_bdd import scenarios

from .steps.cli_commands_steps import *

scenarios('features/doctor_command.feature')
