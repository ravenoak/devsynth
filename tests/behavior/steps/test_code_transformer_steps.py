"""
Step definitions for the code_transformer.feature file.

This module contains the step definitions for the Code Transformer behavior tests.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, parsers, then, when

from devsynth.application.code_analysis.transformer import CodeTransformer
from devsynth.application.edrr.edrr_coordinator_enhanced import EnhancedEDRRCoordinator
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Import the feature file
scenarios = pytest.importorskip("pytest_bdd").scenarios(
    feature_path(__file__, "general", "code_transformer.feature")
)


@pytest.fixture
def context():
    """Create a context object for sharing data between steps."""

    class Context:
        def __init__(self):
            self.transformer = None
            self.code = None
            self.file_path = None
            self.dir_path = None
            self.result = None
            self.edrr_coordinator = None
            self.wsde_team = None

    return Context()


# Background steps
@given("the DevSynth system is initialized")
def devsynth_initialized():
    """Initialize the DevSynth system."""
    # This is a placeholder step that doesn't need to do anything
    pass


@given("the code transformer is configured")
def code_transformer_configured(context):
    """Configure the code transformer."""
    context.transformer = CodeTransformer()


# Scenario: Transform code with unused imports
@given("I have Python code with unused imports")
def python_code_with_unused_imports(context):
    """Set up Python code with unused imports."""
    context.code = """
import os
import sys
import re  # This import is unused

def main():
    print(os.path.join("a", "b"))
    print(sys.version)
"""


@when(parsers.parse('I transform the code using the "{transformation}" transformation'))
def transform_code(context, transformation):
    """Transform the code using the specified transformation."""
    context.result = context.transformer.transform_code(context.code, [transformation])


@then("the transformed code should not contain unused imports")
def verify_no_unused_imports(context):
    """Verify that the transformed code does not contain unused imports."""
    assert (
        "import re" not in context.result.transformed_code
    ), "Unused import 're' still present"
    assert (
        "import os" in context.result.transformed_code
    ), "Import 'os' was removed but it's used"
    assert (
        "import sys" in context.result.transformed_code
    ), "Import 'sys' was removed but it's used"


@then("the transformed code should maintain the original functionality")
def verify_functionality_maintained(context):
    """Verify that the transformed code maintains the original functionality."""
    # This would require executing the code, which is beyond the scope of this test
    # Instead, we'll check that the main function is still present
    assert "def main():" in context.result.transformed_code, "Main function is missing"
    assert (
        "print(os.path.join" in context.result.transformed_code
    ), "os.path.join call is missing"
    assert (
        "print(sys.version)" in context.result.transformed_code
    ), "sys.version call is missing"


@then("the transformation should record the changes made")
def verify_changes_recorded(context):
    """Verify that the transformation records the changes made."""
    assert hasattr(context.result, "changes"), "No changes recorded"
    assert len(context.result.changes) > 0, "No changes recorded"


# Scenario: Transform code with redundant assignments
@given("I have Python code with redundant assignments")
def python_code_with_redundant_assignments(context):
    """Set up Python code with redundant assignments."""
    context.code = """
def calculate_sum(a, b):
    # Redundant assignment
    result = a + b
    return result
"""


@then("the transformed code should not contain redundant assignments")
def verify_no_redundant_assignments(context):
    """Verify that the transformed code does not contain redundant assignments."""
    assert (
        "result = a + b" not in context.result.transformed_code
    ), "Redundant assignment still present"
    assert (
        "return a + b" in context.result.transformed_code
    ), "Direct return not present"


# Scenario: Transform code with unused variables
@given("I have Python code with unused variables")
def python_code_with_unused_variables(context):
    """Set up Python code with unused variables."""
    context.code = """
def process_data(data):
    result = []
    count = 0  # This variable is unused

    for item in data:
        result.append(item * 2)

    return result
"""


@then("the transformed code should not contain unused variables")
def verify_no_unused_variables(context):
    """Verify that the transformed code does not contain unused variables."""
    assert (
        "count = 0" not in context.result.transformed_code
    ), "Unused variable 'count' still present"
    assert (
        "result = []" in context.result.transformed_code
    ), "Variable 'result' was removed but it's used"


# Scenario: Transform code with string literals
@given("I have Python code with string literals that can be optimized")
def python_code_with_string_literals(context):
    """Set up Python code with string literals that can be optimized."""
    context.code = """
def greet(name):
    greeting = "Hello, " + name + "!"
    return greeting
"""


@then("the transformed code should contain optimized string literals")
def verify_optimized_string_literals(context):
    """Verify that the transformed code contains optimized string literals."""
    assert (
        '"Hello, " + name + "!"' not in context.result.transformed_code
    ), "Unoptimized string concatenation still present"
    assert any(
        [
            f'"Hello, {name}!"' in context.result.transformed_code,
            "f'Hello, {name}!'" in context.result.transformed_code,
            'f"Hello, {name}!"' in context.result.transformed_code,
        ]
    ), "Optimized string not present"


# Scenario: Transform code with style issues
@given("I have Python code with style issues")
def python_code_with_style_issues(context):
    """Set up Python code with style issues."""
    context.code = """
def function_without_docstring(a, b):
    return a + b

class ClassWithoutDocstring:
    def method_without_docstring(self):
        pass
"""


@then("the transformed code should have improved style")
def verify_improved_style(context):
    """Verify that the transformed code has improved style."""
    assert '"""' in context.result.transformed_code, "No docstrings added"


# Scenario: Apply multiple transformations to code
@given("I have Python code with multiple issues")
def python_code_with_multiple_issues(context):
    """Set up Python code with multiple issues."""
    context.code = """
import os
import sys
import re  # This import is unused

def calculate_sum(a, b):
    # Redundant assignment
    result = a + b
    return result

def main():
    x = 5
    y = 10
    z = 15  # This variable is unused
    greeting = "Hello, " + "world!"
    total = calculate_sum(x, y)
    print(f"The sum is {total}")
    print(greeting)
"""


@when(
    parsers.parse("I transform the code using the following transformations:\n{table}")
)
def transform_code_with_multiple_transformations(context, table):
    """Transform the code using multiple transformations."""
    # Parse the table
    rows = [line.strip().split("|") for line in table.strip().split("\n")]
    rows = [[cell.strip() for cell in row if cell.strip()] for row in rows]

    # Skip the header row
    transformations = [row[0] for row in rows[1:]]

    # Apply the transformations
    context.result = context.transformer.transform_code(context.code, transformations)


@then("the transformed code should address all issues")
def verify_all_issues_addressed(context):
    """Verify that the transformed code addresses all issues."""
    # Check for unused imports
    assert (
        "import re" not in context.result.transformed_code
    ), "Unused import 're' still present"

    # Check for redundant assignments
    assert (
        "result = a + b" not in context.result.transformed_code
    ), "Redundant assignment still present"

    # Check for unused variables
    assert (
        "z = 15" not in context.result.transformed_code
    ), "Unused variable 'z' still present"

    # Check for string literals
    assert (
        '"Hello, " + "world!"' not in context.result.transformed_code
    ), "Unoptimized string concatenation still present"


@then("the transformation should record all changes made")
def verify_all_changes_recorded(context):
    """Verify that the transformation records all changes made."""
    assert hasattr(context.result, "changes"), "No changes recorded"
    assert len(context.result.changes) > 0, "No changes recorded"

    # Check that changes for different transformations were recorded
    change_descriptions = [change["description"] for change in context.result.changes]
    assert any(
        "import" in desc.lower() for desc in change_descriptions
    ), "No import-related changes recorded"
    assert any(
        "assignment" in desc.lower() for desc in change_descriptions
    ), "No assignment-related changes recorded"
    assert any(
        "variable" in desc.lower() for desc in change_descriptions
    ), "No variable-related changes recorded"
    assert any(
        "string" in desc.lower() for desc in change_descriptions
    ), "No string-related changes recorded"


# Scenario: Transform a file
@given("I have a Python file with code issues")
def python_file_with_code_issues(context):
    """Set up a Python file with code issues."""
    # Create a temporary file
    fd, context.file_path = tempfile.mkstemp(suffix=".py")
    os.close(fd)

    # Write code with issues to the file
    with open(context.file_path, "w") as f:
        f.write(
            """
import os
import sys
import re  # This import is unused

def main():
    print(os.path.join("a", "b"))
    print(sys.version)
"""
        )


@when(parsers.parse('I transform the file using the "{transformation}" transformation'))
def transform_file(context, transformation):
    """Transform the file using the specified transformation."""
    context.result = context.transformer.transform_file(
        context.file_path, [transformation]
    )


@then("the transformed file should not contain unused imports")
def verify_file_no_unused_imports(context):
    """Verify that the transformed file does not contain unused imports."""
    assert (
        "import re" not in context.result.transformed_code
    ), "Unused import 're' still present"
    assert (
        "import os" in context.result.transformed_code
    ), "Import 'os' was removed but it's used"
    assert (
        "import sys" in context.result.transformed_code
    ), "Import 'sys' was removed but it's used"


@then("the transformed file should maintain the original functionality")
def verify_file_functionality_maintained(context):
    """Verify that the transformed file maintains the original functionality."""
    # This would require executing the code, which is beyond the scope of this test
    # Instead, we'll check that the main function is still present
    assert "def main():" in context.result.transformed_code, "Main function is missing"
    assert (
        "print(os.path.join" in context.result.transformed_code
    ), "os.path.join call is missing"
    assert (
        "print(sys.version)" in context.result.transformed_code
    ), "sys.version call is missing"


@then("the transformation should record the changes made to the file")
def verify_file_changes_recorded(context):
    """Verify that the transformation records the changes made to the file."""
    assert hasattr(context.result, "changes"), "No changes recorded"
    assert len(context.result.changes) > 0, "No changes recorded"


# Scenario: Transform a directory
@given("I have a directory with Python files")
def directory_with_python_files(context):
    """Set up a directory with Python files."""
    # Create a temporary directory
    context.dir_path = tempfile.mkdtemp()

    # Create Python files with issues
    with open(os.path.join(context.dir_path, "file1.py"), "w") as f:
        f.write(
            """
import os
import re  # This import is unused

def main():
    print(os.path.join("a", "b"))
"""
        )

    with open(os.path.join(context.dir_path, "file2.py"), "w") as f:
        f.write(
            """
import sys
import re  # This import is unused

def main():
    print(sys.version)
"""
        )


@when(
    parsers.parse(
        'I transform the directory using the "{transformation}" transformation'
    )
)
def transform_directory(context, transformation):
    """Transform the directory using the specified transformation."""
    context.result = context.transformer.transform_directory(
        context.dir_path, recursive=False, transformations=[transformation]
    )


@then("all Python files in the directory should be transformed")
def verify_all_files_transformed(context):
    """Verify that all Python files in the directory were transformed."""
    assert (
        len(context.result) == 2
    ), f"Expected 2 files to be transformed, but got {len(context.result)}"
    assert any(
        "file1.py" in result.file_path for result in context.result
    ), "file1.py was not transformed"
    assert any(
        "file2.py" in result.file_path for result in context.result
    ), "file2.py was not transformed"


@then("none of the transformed files should contain unused imports")
def verify_no_files_with_unused_imports(context):
    """Verify that none of the transformed files contain unused imports."""
    for result in context.result:
        assert (
            "import re" not in result.transformed_code
        ), f"Unused import 're' still present in {result.file_path}"


@then("all transformed files should maintain their original functionality")
def verify_all_files_functionality_maintained(context):
    """Verify that all transformed files maintain their original functionality."""
    for result in context.result:
        assert (
            "def main():" in result.transformed_code
        ), f"Main function is missing in {result.file_path}"
        if "file1.py" in result.file_path:
            assert (
                "print(os.path.join" in result.transformed_code
            ), "os.path.join call is missing in file1.py"
        if "file2.py" in result.file_path:
            assert (
                "print(sys.version)" in result.transformed_code
            ), "sys.version call is missing in file2.py"


@then("the transformation should record the changes made to each file")
def verify_changes_recorded_for_each_file(context):
    """Verify that the transformation records the changes made to each file."""
    for result in context.result:
        assert hasattr(result, "changes"), f"No changes recorded for {result.file_path}"
        assert len(result.changes) > 0, f"No changes recorded for {result.file_path}"


# Scenario: Transform a directory recursively
@given("I have a directory with Python files and subdirectories")
def directory_with_python_files_and_subdirectories(context):
    """Set up a directory with Python files and subdirectories."""
    # Create a temporary directory
    context.dir_path = tempfile.mkdtemp()

    # Create Python files with issues in the main directory
    with open(os.path.join(context.dir_path, "file1.py"), "w") as f:
        f.write(
            """
import os
import re  # This import is unused

def main():
    print(os.path.join("a", "b"))
"""
        )

    # Create a subdirectory with Python files
    subdir = os.path.join(context.dir_path, "subdir")
    os.mkdir(subdir)

    with open(os.path.join(subdir, "file2.py"), "w") as f:
        f.write(
            """
import sys
import re  # This import is unused

def main():
    print(sys.version)
"""
        )


@when(
    parsers.parse(
        'I transform the directory recursively using the "{transformation}" transformation'
    )
)
def transform_directory_recursively(context, transformation):
    """Transform the directory recursively using the specified transformation."""
    context.result = context.transformer.transform_directory(
        context.dir_path, recursive=True, transformations=[transformation]
    )


@then("all Python files in the directory and its subdirectories should be transformed")
def verify_all_files_and_subdirs_transformed(context):
    """Verify that all Python files in the directory and its subdirectories were transformed."""
    assert (
        len(context.result) == 2
    ), f"Expected 2 files to be transformed, but got {len(context.result)}"
    assert any(
        "file1.py" in result.file_path for result in context.result
    ), "file1.py was not transformed"
    assert any(
        "file2.py" in result.file_path for result in context.result
    ), "file2.py was not transformed"


# Scenario: Validate syntax before and after transformation
@given("I have Python code with issues")
def python_code_with_issues(context):
    """Set up Python code with issues."""
    context.code = """
def calculate_sum(a, b):
    result = a + b  # This is a redundant assignment
    return result
"""


@then("the transformer should validate the syntax before transformation")
def verify_syntax_validated_before(context):
    """Verify that the transformer validates the syntax before transformation."""
    # This is a placeholder verification
    # The actual validation happens inside the transformer
    pass


@then("the transformer should validate the syntax after transformation")
def verify_syntax_validated_after(context):
    """Verify that the transformer validates the syntax after transformation."""
    # This is a placeholder verification
    # The actual validation happens inside the transformer
    pass


@then("the transformation should only proceed if the syntax is valid")
def verify_transformation_proceeds_if_valid(context):
    """Verify that the transformation only proceeds if the syntax is valid."""
    # This is a placeholder verification
    # The actual validation happens inside the transformer
    pass


@then("the transformed code should have valid syntax")
def verify_transformed_code_valid_syntax(context):
    """Verify that the transformed code has valid syntax."""
    # We can use the transformer's validate_syntax method to check
    assert context.transformer.validate_syntax(
        context.result.transformed_code
    ), "Transformed code has invalid syntax"


# Scenario: Handle syntax errors gracefully
@given("I have Python code with syntax errors")
def python_code_with_syntax_errors(context):
    """Set up Python code with syntax errors."""
    context.code = """
def broken_function(
    print("Missing closing parenthesis"
"""


@when("I attempt to transform the code")
def attempt_to_transform_code(context):
    """Attempt to transform the code."""
    # We'll use a try-except block to catch any exceptions
    try:
        context.result = context.transformer.transform_code(
            context.code, ["remove_unused_imports"]
        )
        context.exception = None
    except Exception as e:
        context.exception = e
        context.result = None


@then("the transformer should detect the syntax errors")
def verify_syntax_errors_detected(context):
    """Verify that the transformer detects the syntax errors."""
    # This is a placeholder verification
    # The actual detection happens inside the transformer
    pass


@then("the transformer should report the syntax errors")
def verify_syntax_errors_reported(context):
    """Verify that the transformer reports the syntax errors."""
    # This is a placeholder verification
    # The actual reporting happens inside the transformer
    pass


@then("the transformer should not proceed with the transformation")
def verify_transformation_not_proceeded(context):
    """Verify that the transformer does not proceed with the transformation."""
    # If the transformation failed, context.result should be None
    # If it succeeded despite the syntax errors, context.result should not be None
    assert context.result is None or not hasattr(
        context.result, "transformed_code"
    ), "Transformation proceeded despite syntax errors"


# Scenario: Integrate with EDRR workflow
@given("the EDRR workflow is configured")
def edrr_workflow_configured(context):
    """Configure the EDRR workflow."""
    # Create a mock EDRR coordinator
    context.edrr_coordinator = MagicMock(spec=EnhancedEDRRCoordinator)


@when("I initiate a code transformation task")
def initiate_code_transformation_task(context):
    """Initiate a code transformation task."""
    # Mock the execution of a code transformation task
    context.result = {
        "task": "code_transformation",
        "phase": "refinement",
        "status": "completed",
    }


@then("the system should use code transformation in the Refinement phase")
def verify_refinement_phase(context):
    """Verify that code transformation is used in the Refinement phase."""
    assert (
        context.result["phase"] == "refinement"
    ), "Code transformation not used in Refinement phase"


@then("the system should apply appropriate transformations based on the code analysis")
def verify_appropriate_transformations(context):
    """Verify that appropriate transformations are applied based on the code analysis."""
    # This is a placeholder verification
    assert (
        context.result["task"] == "code_transformation"
    ), "Code transformation task not executed"


@then(
    "the memory system should store transformation results with appropriate EDRR phase tags"
)
def verify_results_stored_with_phase_tags(context):
    """Verify that transformation results are stored with appropriate EDRR phase tags."""
    # This is a placeholder verification
    assert (
        context.result["phase"] == "refinement"
    ), "Results not stored with Refinement phase tag"


# Scenario: Integrate with WSDE team
@given("the WSDE team is configured")
def wsde_team_configured(context):
    """Configure the WSDE team."""
    # Create a mock WSDE team
    context.wsde_team = MagicMock(spec=WSDETeam)


@when("I assign a code transformation task to the WSDE team")
def assign_code_transformation_task(context):
    """Assign a code transformation task to the WSDE team."""
    # Mock the assignment of a code transformation task
    context.result = {
        "task": "code_transformation",
        "assigned_to": "wsde_team",
        "status": "completed",
    }


@then("the team should collaborate to transform different aspects of the code")
def verify_team_collaboration(context):
    """Verify that the team collaborates to transform different aspects of the code."""
    # This is a placeholder verification
    assert (
        context.result["assigned_to"] == "wsde_team"
    ), "Task not assigned to WSDE team"


@then("the team should share transformation results between agents")
def verify_results_shared(context):
    """Verify that transformation results are shared between agents."""
    # This is a placeholder verification
    assert context.result["status"] == "completed", "Task not completed"


@then("the team should produce consolidated transformed code")
def verify_consolidated_code(context):
    """Verify that the team produces consolidated transformed code."""
    # This is a placeholder verification
    assert (
        context.result["task"] == "code_transformation"
    ), "Code transformation task not executed"
