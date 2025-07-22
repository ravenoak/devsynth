from pytest_bdd import scenarios, then

from .webui_steps import *  # noqa: F401,F403

scenarios("../features/general/webui_doctor.feature")


@then("the doctor command should be executed")
def check_doctor(webui_context):
    assert webui_context["cli"].doctor_cmd.called
