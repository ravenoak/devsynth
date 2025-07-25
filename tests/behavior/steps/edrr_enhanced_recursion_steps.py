"""Step definitions for the ``edrr_enhanced_recursion.feature`` file."""

from pytest_bdd import scenarios

from .test_edrr_enhanced_recursion_steps import *  # noqa: F401,F403

scenarios("../features/edrr_enhanced_recursion.feature")
