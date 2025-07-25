"""Step definitions for the ``wsde_edrr_integration.feature`` file."""

from pytest_bdd import scenarios

from .test_wsde_edrr_integration_steps import *  # noqa: F401,F403

scenarios("../features/wsde_edrr_integration.feature")
