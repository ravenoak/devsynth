"""Step definitions for the ``micro_edrr_cycle.feature`` file."""

from pytest_bdd import scenarios

from .test_micro_edrr_cycle_steps import *  # noqa: F401,F403

scenarios("../features/micro_edrr_cycle.feature")
