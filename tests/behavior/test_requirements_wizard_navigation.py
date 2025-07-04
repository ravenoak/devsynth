import os
from pytest_bdd import scenarios

from .steps.requirements_wizard_navigation_steps import *  # noqa: F401,F403

# Get the absolute path to the feature file
feature_file = os.path.join(os.path.dirname(__file__), "features", "requirements_wizard_navigation.feature")

# Load the scenarios from the feature file
scenarios(feature_file)
