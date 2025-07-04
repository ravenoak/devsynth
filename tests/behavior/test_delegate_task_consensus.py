import os
from pytest_bdd import scenarios

from .steps.delegate_task_consensus_steps import *  # noqa: F401,F403

# Get the absolute path to the feature file
feature_file = os.path.join(os.path.dirname(__file__), "features", "delegate_task_consensus.feature")

# Load the scenarios from the feature file
scenarios(feature_file)
