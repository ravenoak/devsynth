import os

import pytest
from pytest_bdd import scenarios

from .steps.test_requirements_wizard_navigation_steps import *  # noqa: F401,F403


pytestmark = [pytest.mark.fast]

# Get the absolute path to the feature file
feature_file = os.path.join(
    os.path.dirname(__file__),
    "requirements_wizard",
    "features",
    "general",
    "requirements_wizard_navigation.feature",
)

# Load the scenarios from the feature file
scenarios(feature_file)
