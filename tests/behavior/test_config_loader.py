import os

from pytest_bdd import scenarios

# Import step definitions
from .steps.test_config_loader_steps import *

# Get the absolute path to the feature file
feature_file = os.path.join(
    os.path.dirname(__file__), "features", "general", "config_loader.feature"
)

# Load the scenarios from the feature file
scenarios(feature_file)
