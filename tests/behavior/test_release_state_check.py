"""ReqID: FR-95"""

import os

import pytest
from pytest_bdd import scenarios

feature_file = os.path.join(
    os.path.dirname(__file__),
    "features",
    "release_state_check.feature",
)

scenarios(feature_file)

pytestmark = pytest.mark.fast
