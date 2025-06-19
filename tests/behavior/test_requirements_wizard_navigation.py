from pytest_bdd import scenarios

from .steps.requirements_wizard_navigation_steps import *  # noqa: F401,F403

scenarios("features/requirements_wizard_navigation.feature")
