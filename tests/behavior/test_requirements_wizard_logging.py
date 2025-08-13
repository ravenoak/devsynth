import os

from pytest_bdd import scenarios

feature_file = os.path.join(
    os.path.dirname(__file__),
    "features",
    "general",
    "requirements_wizard_logging.feature",
)

scenarios(feature_file)
