"""Step definitions for the ``edrr_real_llm_integration.feature`` file."""

from pytest_bdd import scenarios

from .test_edrr_real_llm_integration_steps import *  # noqa: F401,F403


scenarios("../features/edrr_real_llm_integration.feature")
