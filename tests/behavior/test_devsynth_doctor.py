import os
from pytest_bdd import scenarios

from .steps.cli_commands_steps import *
from .steps.devsynth_doctor_steps import *

# Get the absolute path to the feature file
feature_file = os.path.join(os.path.dirname(__file__), "features", "devsynth_doctor.feature")

# Load the scenarios from the feature file
scenarios(feature_file)
