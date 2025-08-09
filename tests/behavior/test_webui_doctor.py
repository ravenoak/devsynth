from pytest_bdd import scenarios

from .steps.test_webui_doctor_steps import *  # noqa: F401,F403
from .steps.test_webui_steps import *  # noqa: F401,F403

scenarios("general/webui_doctor.feature")
