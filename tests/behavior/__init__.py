"""DevSynth Behavior Test Package

This package contains behavior-driven tests for the DevSynth project.
"""

# Import step modules so their definitions are registered
try:
    from .steps import spec_command_steps  # noqa: F401
except ImportError as e:
    print(f"Warning: Could not import spec_command_steps: {e}")

try:
    from .steps import code_command_steps  # noqa: F401
except ImportError as e:
    print(f"Warning: Could not import code_command_steps: {e}")
