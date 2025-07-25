"""Step definitions for the ``edrr_coordinator.feature`` file.

This module previously contained minimal stub implementations that
resulted in "step definition not found" errors for many scenarios.  To
reuse the comprehensive step implementations while keeping this module
importable, it now simply re-exports everything from
``test_edrr_coordinator_steps``.
"""

from .test_edrr_coordinator_steps import *  # noqa: F401,F403
