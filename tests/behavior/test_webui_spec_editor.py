import os
from pytest_bdd import scenarios

from .steps.webui_spec_editor_steps import *  # noqa: F401,F403
from .steps.webui_steps import *  # noqa: F401,F403

# Get the absolute path to the feature file
feature_file = os.path.join(os.path.dirname(__file__), "features", "general", "webui_spec_editor.feature")

# Load the scenarios from the feature file
scenarios(feature_file)
