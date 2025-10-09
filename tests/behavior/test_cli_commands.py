"""Test file for CLI Command Execution feature."""

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

from .steps.cli_commands_steps import *
from .steps.test_delegate_task_steps import *
from .steps.test_doctor_command_steps import *
from .steps.test_edrr_cycle_steps import *

# Define feature file paths
FEATURE_FILE = feature_path(__file__, "general", "cli_commands.feature")
EDRR_FEATURE = feature_path(__file__, "general", "edrr_cycle.feature")
DELEGATE_FEATURE = feature_path(__file__, "general", "delegate_task.feature")
DOCTOR_FEATURE = feature_path(__file__, "general", "doctor_command.feature")

# Mark all tests as requiring CLI resource

pytestmark = [
    pytest.mark.fast,
    pytest.mark.requires_resource("cli"),
]

# Load all scenarios from the feature files
scenarios(FEATURE_FILE)
scenarios(EDRR_FEATURE)
scenarios(DELEGATE_FEATURE)
scenarios(DOCTOR_FEATURE)


# The test functions below are no longer needed as scenarios() will automatically
# generate test functions for each scenario in the feature files.
# The naming convention will be test_<scenario_name_with_underscores>

# For documentation purposes, we keep the docstrings of what each scenario tests
"""
Scenarios in cli_commands.feature:

1. Display help information
   Test displaying help information.
   ReqID: N/A

2. Initialize a project with path parameter
   Test initializing a project with a path parameter.
   ReqID: N/A

3. Generate specifications with custom requirements file
   Test generating specifications with a custom requirements file.
   ReqID: N/A

4. Generate tests with custom specification file
   Test generating tests with a custom specification file.
   ReqID: N/A

5. Generate code without parameters
   Test generating code without parameters.
   ReqID: N/A

6. Run with specific target
   Test running with a specific target.
   ReqID: N/A

7. Configure with key and value
   Test configuring with a key and value.
   ReqID: N/A

8. View configuration for specific key
   Test viewing configuration for a specific key.
   ReqID: N/A

9. View all configuration
   Test viewing all configuration.
   ReqID: N/A

10. Handle invalid command
    Test handling an invalid command.
    ReqID: N/A

11. Serve API on custom port
    Test serving the API on a custom port.
    ReqID: N/A

Scenarios in edrr_cycle.feature:

1. Run EDRR cycle with manifest file
   Test running the edrr-cycle command with a manifest.
   ReqID: N/A

2. Handle missing manifest file
   Test running the edrr-cycle command with a missing manifest file.
   ReqID: N/A

Scenarios in delegate_task.feature:

1. Delegate a team task to multiple agents
   Test delegating a collaborative task to multiple agents.
   ReqID: N/A

Scenarios in doctor_command.feature:

1. Validate configuration using the check alias
   Test doctor command via the check alias.
   ReqID: N/A
"""
