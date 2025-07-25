"""Step definitions for the ``edrr_coordinator.feature`` file."""

from pytest_bdd import scenarios

from .test_edrr_coordinator_steps import *  # noqa: F401,F403


scenarios("../features/edrr_coordinator.feature")
