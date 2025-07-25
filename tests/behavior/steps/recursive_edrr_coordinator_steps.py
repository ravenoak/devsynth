"""Step definitions for the ``recursive_edrr_coordinator.feature`` file."""

from pytest_bdd import scenarios

from .test_recursive_edrr_coordinator_steps import *  # noqa: F401,F403

scenarios("../features/recursive_edrr_coordinator.feature")
