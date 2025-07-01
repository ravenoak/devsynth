from pytest_bdd import scenarios

from .steps.setup_wizard_steps import *  # noqa: F401,F403

scenarios("features/setup_wizard.feature")
