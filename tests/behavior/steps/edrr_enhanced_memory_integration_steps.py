"""Step definitions for the ``edrr_enhanced_memory_integration.feature`` file."""

from pytest_bdd import scenarios

from .test_edrr_enhanced_memory_integration_steps import *  # noqa: F401,F403

scenarios("../features/edrr_enhanced_memory_integration.feature")
