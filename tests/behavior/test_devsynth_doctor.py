from pytest_bdd import scenarios

from .steps.cli_commands_steps import *
from .steps.devsynth_doctor_steps import *

scenarios('features/devsynth_doctor.feature')
