"""Step definitions for the ``edrr_enhanced_phase_transitions.feature`` file."""

from pytest_bdd import scenarios

from .test_edrr_enhanced_phase_transitions_steps import *  # noqa: F401,F403

scenarios("../features/edrr_enhanced_phase_transitions.feature")
