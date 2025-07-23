from pytest_bdd import scenarios
import os

# Import step definitions
from .steps.config_loader_steps import *

# Get the absolute path to the feature file
feature_file = os.path.join(os.path.dirname(__file__), "features", "general", "config_loader.feature")

# Load the scenarios from the feature file
scenarios(feature_file)
