import os
from pytest_bdd import scenarios

from .steps.cli_commands_steps import *  # noqa: F401,F403
from .steps.doctor_missing_env_steps import *  # noqa: F401,F403

# Get the absolute path to the feature file
feature_file = os.path.join(os.path.dirname(__file__), "features", "doctor_missing_env.feature")

# Load the scenarios from the feature file
scenarios(feature_file)
