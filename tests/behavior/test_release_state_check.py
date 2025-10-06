"""ReqID: FR-95"""

import os

import pytest
from pytest_bdd import scenarios

from tests.behavior.steps import release_state_steps  # noqa: F401


pytestmark = [pytest.mark.fast]

feature_file = os.path.join(
    os.path.dirname(__file__),
    "features",
    "general",
    "release_state_check.feature",
)

scenarios(feature_file)
