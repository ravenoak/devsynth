from pytest_bdd import scenarios

from .steps.webui_spec_editor_extended_steps import *  # noqa: F401,F403

scenarios("general/webui_spec_editor_extended.feature")