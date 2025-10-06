import pytest
from pytest_bdd import scenarios

from .steps.test_dialectical_reasoning_memory_persistence_steps import *  # noqa: F401,F403


pytestmark = [pytest.mark.fast]

scenarios("features/general/dialectical_reasoning_memory_persistence.feature")
