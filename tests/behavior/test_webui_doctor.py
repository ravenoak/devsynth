from pytest_bdd import scenarios

from .steps.webui_steps import *  # noqa: F401,F403
from .steps.webui_doctor_steps import *  # noqa: F401,F403

scenarios("features/webui_doctor.feature")
