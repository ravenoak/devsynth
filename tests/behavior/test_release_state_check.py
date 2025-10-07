"""ReqID: FR-95"""

import pytest
from pytest_bdd import scenarios

from tests.behavior.steps import release_state_steps  # noqa: F401

from tests.behavior.feature_paths import feature_path


pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "release_state_check.feature"))
