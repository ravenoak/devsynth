"""Test file for extended cross-interface consistency BDD tests."""

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

# Import the fixture
from tests.behavior.steps.test_cross_interface_consistency_extended_steps import (
    cross_interface_context,
)

pytestmark = [pytest.mark.fast]

# Register the scenarios from the feature file using canonical asset paths.
scenarios(
    feature_path(__file__, "general", "cross_interface_consistency_extended.feature")
)


# Define step definitions directly in this file
@given("the CLI, WebUI, and Agent API share a UXBridge")
def shared_bridge_setup(cross_interface_context):
    """Set up shared UXBridge for all interfaces."""
    # Return the context which already has all interfaces set up
    return cross_interface_context


@when(parsers.parse("{command} is invoked from all interfaces"))
def invoke_command_all_interfaces(cross_interface_context, command):
    """Invoke the specified command from all interfaces."""
    from tests.behavior.steps.test_cross_interface_consistency_extended_steps import (
        invoke_command_all_interfaces as impl,
    )

    return impl(cross_interface_context, command)


@when("an error occurs during command execution")
def simulate_error(cross_interface_context):
    """Simulate an error during command execution."""
    from tests.behavior.steps.test_cross_interface_consistency_extended_steps import (
        simulate_error as impl,
    )

    return impl(cross_interface_context)


@when("user input is required during command execution")
def simulate_user_input(cross_interface_context):
    """Simulate a scenario where user input is required."""
    from tests.behavior.steps.test_cross_interface_consistency_extended_steps import (
        simulate_user_input as impl,
    )

    return impl(cross_interface_context)


@then("all invocations pass identical arguments")
def verify_identical_arguments(cross_interface_context):
    """Verify that all interfaces pass identical arguments to the command."""
    from tests.behavior.steps.test_cross_interface_consistency_extended_steps import (
        verify_identical_arguments as impl,
    )

    return impl(cross_interface_context)


@then("the command behavior is consistent across interfaces")
def verify_consistent_behavior(cross_interface_context):
    """Verify that the command behavior is consistent across interfaces."""
    from tests.behavior.steps.test_cross_interface_consistency_extended_steps import (
        verify_consistent_behavior as impl,
    )

    return impl(cross_interface_context)


@then("all interfaces handle the error consistently")
def verify_consistent_error_handling(cross_interface_context):
    """Verify that all interfaces handle errors consistently."""
    from tests.behavior.steps.test_cross_interface_consistency_extended_steps import (
        verify_consistent_error_handling as impl,
    )

    return impl(cross_interface_context)


@then("appropriate error messages are displayed")
def verify_error_messages(cross_interface_context):
    """Verify that appropriate error messages are displayed."""
    from tests.behavior.steps.test_cross_interface_consistency_extended_steps import (
        verify_error_messages as impl,
    )

    return impl(cross_interface_context)


@then("all interfaces prompt for input consistently")
def verify_consistent_input_prompting(cross_interface_context):
    """Verify that all interfaces prompt for input consistently."""
    from tests.behavior.steps.test_cross_interface_consistency_extended_steps import (
        verify_consistent_input_prompting as impl,
    )

    return impl(cross_interface_context)


@then("the input is processed correctly")
def verify_input_processing(cross_interface_context):
    """Verify that user input is processed correctly."""
    from tests.behavior.steps.test_cross_interface_consistency_extended_steps import (
        verify_input_processing as impl,
    )

    return impl(cross_interface_context)
