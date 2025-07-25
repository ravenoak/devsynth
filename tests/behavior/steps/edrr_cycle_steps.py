"""Step definitions for the ``edrr_cycle.feature`` file."""

from pytest_bdd import scenarios

from .test_edrr_cycle_steps import *  # noqa: F401,F403


scenarios("../features/edrr_cycle.feature")
