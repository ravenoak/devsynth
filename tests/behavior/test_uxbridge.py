import pytest
from pytest_bdd import scenarios

from .steps.test_uxbridge_steps import *  # noqa: F401,F403


pytestmark = [pytest.mark.fast]

scenarios("features/general/uxbridge.feature")
