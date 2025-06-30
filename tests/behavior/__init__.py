"""DevSynth Behavior Test Package

This package contains behavior-driven tests for the DevSynth project.
"""

from pytest_bdd import scenarios

# Automatically load scenarios for CLI commands not covered by dedicated tests
scenarios("features/spec_command.feature")
scenarios("features/code_command.feature")

# Import step modules so their definitions are registered
from .steps import spec_command_steps  # noqa: F401
from .steps import code_command_steps  # noqa: F401
