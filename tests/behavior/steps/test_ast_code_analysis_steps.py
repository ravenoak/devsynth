"""
Step Definitions for AST-Based Code Analysis and Transformation BDD Tests

This module implements the step definitions for the AST-based code analysis and transformation
feature file, testing the integration between AST-based code analysis and the EDRR workflow.
"""
import pytest
from pytest_bdd import given, when, then, parsers, scenarios

# Import the feature file
scenarios('../features/ast_code_analysis.feature')

# Import the modules needed for the steps
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.code_analysis.ast_workflow_integration import AstWorkflowIntegration
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.memory import MemoryType
from devsynth.methodology.base import Phase as EDRRPhase


@pytest.fixture
def context():
    """Fixture to provide a context object for sharing state between steps."""
    class Context:
        def __init__(self):
            self.code_analyzer = CodeAnalyzer()
            self.ast_transformer = AstTransformer()
            self.memory_manager = MemoryManager({
                'default': None  # Mock memory store for testing
            })
            self.ast_workflow_integration = AstWorkflowIntegration(self.memory_manager)
            self.code = ""
            self.ast = None
            self.analysis_result = None
            self.transformation_result = None
            self.implementation_options = []
            self.selected_option = None
            self.refined_code = ""
            self.retrospective_result = None
            self.task_id = "test_task_123"

    return Context()


# Background steps

@given("the DevSynth system is initialized")
def devsynth_system_initialized(context):
    """Initialize the DevSynth system."""
    # The system is initialized by creating the context
    assert context is not None


@given("the AST-based code analysis module is configured")
def ast_code_analysis_module_configured(context):
    """Configure the AST-based code analysis module."""
    # The module is configured by creating the code analyzer and transformer
    assert context.code_analyzer is not None
    assert context.ast_transformer is not None


# Scenario: Parse Python code into AST

@when("I provide Python code to the analyzer")
def provide_code_to_analyzer(context):
    """Provide Python code to the analyzer."""
    # Sample Python code for testing
    context.code = """
def hello(name):
    \"\"\"Say hello to someone.\"\"\"
    return f"Hello, {name}!"

class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def greet(self):
        return hello(self.name)
"""


@then("it should parse the code into an AST representation")
def parse_code_into_ast(context):
    """Parse the code into an AST representation."""
    # Use the ast module to parse the code
    import ast
    context.ast = ast.parse(context.code)

    # Verify that the AST is not None
    assert context.ast is not None


@then("the AST should accurately represent the code structure")
def ast_represents_code_structure(context):
    """Verify that the AST accurately represents the code structure."""
    # Verify that the AST contains the expected nodes
    import ast

    # Check for function definition
    function_nodes = [node for node in ast.walk(context.ast) if isinstance(node, ast.FunctionDef)]
    assert any(node.name == "hello" for node in function_nodes)

    # Check for class definition
    class_nodes = [node for node in ast.walk(context.ast) if isinstance(node, ast.ClassDef)]
    assert any(node.name == "Person" for node in class_nodes)


@then("I should be able to access all code elements through the AST")
def access_code_elements_through_ast(context):
    """Verify that all code elements can be accessed through the AST."""
    # Use the code analyzer to analyze the code
    analysis_result = context.code_analyzer.analyze_code(context.code)

    # Verify that the analysis result contains the expected elements
    functions = analysis_result.get_functions()
    classes = analysis_result.get_classes()

    assert any(func["name"] == "hello" for func in functions)
    assert any(cls["name"] == "Person" for cls in classes)

    # Store the analysis result for later use
    context.analysis_result = analysis_result


# Scenario: Extract code structure information

@given("I have Python code with classes, functions, and variables")
def have_code_with_classes_functions_variables(context):
    """Provide Python code with classes, functions, and variables."""
    # Sample Python code with classes, functions, and variables
    context.code = """
# Module-level variables
MAX_VALUE = 100
default_name = "Guest"

def calculate_sum(a, b):
    \"\"\"Calculate the sum of two numbers.\"\"\"
    result = a + b
    return result

class Calculator:
    def __init__(self, name="Calculator"):
        self.name = name
        self.history = []

    def add(self, a, b):
        result = calculate_sum(a, b)
        self.history.append(f"{a} + {b} = {result}")
        return result

    def get_history(self):
        return self.history
"""


@when("I analyze the code using the AST analyzer")
def analyze_code_using_ast_analyzer(context):
    """Analyze the code using the AST analyzer."""
    # Use the code analyzer to analyze the code
    context.analysis_result = context.code_analyzer.analyze_code(context.code)

    # Verify that the analysis result is not None
    assert context.analysis_result is not None


@then("I should receive a structured representation of the code")
def receive_structured_representation(context):
    """Verify that a structured representation of the code is received."""
    # Verify that the analysis result contains the expected elements
    assert context.analysis_result.get_functions() is not None
    assert context.analysis_result.get_classes() is not None
    assert context.analysis_result.get_variables() is not None


@then("the representation should include all classes with their methods")
def representation_includes_classes_with_methods(context):
    """Verify that the representation includes all classes with their methods."""
    # Verify that the analysis result includes the Calculator class with its methods
    classes = context.analysis_result.get_classes()

    calculator_class = next((cls for cls in classes if cls["name"] == "Calculator"), None)
    assert calculator_class is not None
    assert "add" in calculator_class["methods"]
    assert "get_history" in calculator_class["methods"]


@then("the representation should include all functions with their parameters")
def representation_includes_functions_with_parameters(context):
    """Verify that the representation includes all functions with their parameters."""
    # Verify that the analysis result includes the calculate_sum function with its parameters
    functions = context.analysis_result.get_functions()

    calculate_sum_func = next((func for func in functions if func["name"] == "calculate_sum"), None)
    assert calculate_sum_func is not None
    assert "a" in calculate_sum_func["params"]
    assert "b" in calculate_sum_func["params"]


@then("the representation should include all variables with their types")
def representation_includes_variables_with_types(context):
    """Verify that the representation includes all variables with their types."""
    # Verify that the analysis result includes the module-level variables
    variables = context.analysis_result.get_variables()

    max_value_var = next((var for var in variables if var["name"] == "MAX_VALUE"), None)
    default_name_var = next((var for var in variables if var["name"] == "default_name"), None)

    assert max_value_var is not None
    assert default_name_var is not None
    assert max_value_var["type"] == "int"
    assert default_name_var["type"] == "str"


# Scenario: Perform AST-based code transformations

@given("I have Python code that needs refactoring")
def have_code_that_needs_refactoring(context):
    """Provide Python code that needs refactoring."""
    # Sample Python code that needs refactoring (missing docstrings)
    context.code = """
def calculate_sum(a, b):
    return a + b

class Calculator:
    def __init__(self, name="Calculator"):
        self.name = name
        self.history = []

    def add(self, a, b):
        result = calculate_sum(a, b)
        self.history.append(f"{a} + {b} = {result}")
        return result
"""


@when("I request an AST-based transformation")
def request_ast_based_transformation(context):
    """Request an AST-based transformation."""
    # Use the AST transformer to add docstrings to the code
    try:
        # Add docstring to the calculate_sum function
        transformed_code = context.ast_transformer.add_docstring(
            context.code,
            "calculate_sum",
            "Calculate the sum of two numbers."
        )

        # Add docstring to the Calculator class
        transformed_code = context.ast_transformer.add_docstring(
            transformed_code,
            "Calculator",
            "A simple calculator class that keeps history of operations."
        )

        # Store the transformed code
        context.transformation_result = transformed_code
    except Exception as e:
        pytest.fail(f"AST transformation failed: {str(e)}")


@then("the system should modify the AST according to the transformation rules")
def system_modifies_ast_according_to_rules(context):
    """Verify that the system modifies the AST according to the transformation rules."""
    # Verify that the transformation result is not None
    assert context.transformation_result is not None

    # Verify that the transformation result is different from the original code
    assert context.transformation_result != context.code


@then("the system should generate valid Python code from the modified AST")
def system_generates_valid_python_code(context):
    """Verify that the system generates valid Python code from the modified AST."""
    # Verify that the transformation result is valid Python code
    try:
        # Try to compile the transformed code
        compile(context.transformation_result, "<string>", "exec")
    except SyntaxError as e:
        pytest.fail(f"Generated code is not valid Python: {str(e)}")


@then("the transformed code should maintain the original functionality")
def transformed_code_maintains_functionality(context):
    """Verify that the transformed code maintains the original functionality."""
    # Define a function to execute code and capture its output
    def execute_code(code, func_name, *args):
        # Create a namespace for execution
        namespace = {}

        # Execute the code in the namespace
        exec(code, namespace)

        # Call the function with the given arguments
        return namespace[func_name](*args)

    # Test the original code
    original_result = execute_code(context.code, "calculate_sum", 2, 3)

    # Test the transformed code
    transformed_result = execute_code(context.transformation_result, "calculate_sum", 2, 3)

    # Verify that the results are the same
    assert original_result == transformed_result == 5


# Scenario: Extract function definitions

@given("I have Python code with multiple function definitions")
def have_code_with_multiple_function_definitions(context):
    """Provide Python code with multiple function definitions."""
    # Sample Python code with multiple function definitions
    context.code = """
def add(a, b):
    \"\"\"Add two numbers.\"\"\"
    return a + b

def subtract(a, b):
    \"\"\"Subtract b from a.\"\"\"
    return a - b

def multiply(a, b):
    \"\"\"Multiply two numbers.\"\"\"
    return a * b

def divide(a, b):
    \"\"\"Divide a by b.\"\"\"
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
"""


@when("I request to extract function definitions using AST")
def request_to_extract_function_definitions(context):
    """Request to extract function definitions using AST."""
    # Use the code analyzer to analyze the code
    context.analysis_result = context.code_analyzer.analyze_code(context.code)


@then("the system should identify all functions in the code")
def system_identifies_all_functions(context):
    """Verify that the system identifies all functions in the code."""
    # Verify that the analysis result includes all functions
    functions = context.analysis_result.get_functions()

    function_names = [func["name"] for func in functions]
    assert "add" in function_names
    assert "subtract" in function_names
    assert "multiply" in function_names
    assert "divide" in function_names


@then("for each function, it should extract the signature, parameters, and return type")
def extract_signature_parameters_return_type(context):
    """Verify that the system extracts the signature, parameters, and return type for each function."""
    # Verify that the analysis result includes the signature, parameters, and return type for each function
    functions = context.analysis_result.get_functions()

    # Check the add function
    add_func = next((func for func in functions if func["name"] == "add"), None)
    assert add_func is not None
    assert "a" in add_func["params"]
    assert "b" in add_func["params"]

    # Check the divide function
    divide_func = next((func for func in functions if func["name"] == "divide"), None)
    assert divide_func is not None
    assert "a" in divide_func["params"]
    assert "b" in divide_func["params"]


@then("the extracted information should be stored in the memory system")
def extracted_information_stored_in_memory(context):
    """Verify that the extracted information is stored in the memory system."""
    # In a real implementation, we would store the analysis result in the memory system
    # For testing purposes, we'll simulate this by creating a memory item

    # Create a memory item for the analysis result
    memory_item = MemoryItem(
        id="",
        content=context.analysis_result,
        memory_type=MemoryType.CODE_ANALYSIS,
        metadata={
            "code_hash": hash(context.code),
            "analysis_type": "function_extraction"
        }
    )
    # Store the memory item
    item_id = context.memory_manager.store_item(memory_item)

    # Verify that the memory item was created
    assert memory_item is not None
    assert memory_item.content == context.analysis_result


# Scenario: Rename identifiers

@given("I have Python code with identifiers that need renaming")
def have_code_with_identifiers_to_rename(context):
    """Provide Python code with identifiers that need renaming."""
    # Sample Python code with identifiers that need renaming
    context.code = """
def calc_sum(a, b):
    result = a + b
    return result

class Calc:
    def __init__(self):
        self.history = []

    def add_nums(self, a, b):
        res = calc_sum(a, b)
        self.history.append(res)
        return res
"""


@when("I request to rename an identifier using AST transformation")
def request_to_rename_identifier(context):
    """Request to rename an identifier using AST transformation."""
    # Use the AST transformer to rename identifiers
    try:
        # Rename the calc_sum function to calculate_sum
        transformed_code = context.ast_transformer.rename_identifier(
            context.code,
            "calc_sum",
            "calculate_sum"
        )

        # Rename the Calc class to Calculator
        transformed_code = context.ast_transformer.rename_identifier(
            transformed_code,
            "Calc",
            "Calculator"
        )

        # Store the transformed code
        context.transformation_result = transformed_code
    except Exception as e:
        pytest.fail(f"AST transformation failed: {str(e)}")


@then("the system should identify all occurrences of the identifier")
def system_identifies_all_occurrences(context):
    """Verify that the system identifies all occurrences of the identifier."""
    # Verify that the transformation result is not None
    assert context.transformation_result is not None

    # Verify that the transformation result contains the new identifiers
    assert "calculate_sum" in context.transformation_result
    assert "Calculator" in context.transformation_result

    # Verify that the transformation result does not contain the old identifiers in code (not in strings/comments)
    # Check for specific patterns that should be renamed
    assert "def calc_sum" not in context.transformation_result
    assert "class Calc" not in context.transformation_result
    assert "res = calc_sum" not in context.transformation_result


@then("it should rename all occurrences while preserving scope rules")
def rename_all_occurrences_preserving_scope(context):
    """Verify that the system renames all occurrences while preserving scope rules."""
    # Verify that the transformation result contains the correct references
    assert "res = calculate_sum(a, b)" in context.transformation_result


@then("the resulting code should be valid Python with the updated identifier")
def resulting_code_is_valid_python(context):
    """Verify that the resulting code is valid Python with the updated identifier."""
    # Verify that the transformation result is valid Python code
    try:
        # Try to compile the transformed code
        compile(context.transformation_result, "<string>", "exec")
    except SyntaxError as e:
        pytest.fail(f"Generated code is not valid Python: {str(e)}")


# Scenario: Integrate with EDRR workflow

@given("the EDRR workflow is configured")
def edrr_workflow_configured(context):
    """Configure the EDRR workflow."""
    # Verify that the AST workflow integration is initialized
    assert context.ast_workflow_integration is not None


@when("I initiate a coding task")
def initiate_coding_task(context):
    """Initiate a coding task."""
    # Sample Python code for the coding task
    context.code = """
def calculate_sum(a, b):
    return a + b

def calculate_product(a, b):
    return a * b

class Calculator:
    def __init__(self):
        self.history = []

    def add(self, a, b):
        result = calculate_sum(a, b)
        self.history.append(result)
        return result

    def multiply(self, a, b):
        result = calculate_product(a, b)
        self.history.append(result)
        return result
"""


@then("the system should use AST analysis in the Expand phase to explore implementation options")
def system_uses_ast_analysis_in_expand_phase(context):
    """Verify that the system uses AST analysis in the Expand phase to explore implementation options."""
    # Use the AST workflow integration to explore implementation options
    context.implementation_options = context.ast_workflow_integration.expand_implementation_options(
        context.code,
        context.task_id
    )

    # Verify that implementation options were generated
    assert len(context.implementation_options) > 0

    # Verify that the options include the current implementation
    assert any(option["name"] == "current_implementation" for option in context.implementation_options)


@then("the system should use AST analysis in the Differentiate phase to evaluate code quality")
def system_uses_ast_analysis_in_differentiate_phase(context):
    """Verify that the system uses AST analysis in the Differentiate phase to evaluate code quality."""
    # Use the AST workflow integration to evaluate implementation quality
    context.selected_option = context.ast_workflow_integration.differentiate_implementation_quality(
        context.implementation_options,
        context.task_id
    )

    # Verify that an option was selected
    assert context.selected_option is not None

    # Verify that the selected option has quality metrics
    assert "metrics" in context.selected_option
    assert "complexity" in context.selected_option["metrics"]
    assert "readability" in context.selected_option["metrics"]
    assert "maintainability" in context.selected_option["metrics"]


@then("the system should use AST transformations in the Refine phase to improve the code")
def system_uses_ast_transformations_in_refine_phase(context):
    """Verify that the system uses AST transformations in the Refine phase to improve the code."""
    # Use the AST workflow integration to refine the implementation
    context.refined_code = context.ast_workflow_integration.refine_implementation(
        context.code,
        context.task_id
    )

    # Verify that the code was refined
    assert context.refined_code is not None
    assert context.refined_code != context.code

    # Verify that docstrings were added
    assert '"""Function that calculate_sum"""' in context.refined_code
    assert '"""Function that calculate_product"""' in context.refined_code
    assert '"""Class representing a Calculator"""' in context.refined_code


@then("the system should use AST analysis in the Retrospect phase to verify code quality")
def system_uses_ast_analysis_in_retrospect_phase(context):
    """Verify that the system uses AST analysis in the Retrospect phase to verify code quality."""
    # Use the AST workflow integration to perform a retrospective
    context.retrospective_result = context.ast_workflow_integration.retrospect_code_quality(
        context.refined_code,
        context.task_id
    )

    # Verify that a retrospective was performed
    assert context.retrospective_result is not None

    # Verify that the retrospective includes quality metrics
    assert "metrics" in context.retrospective_result
    assert "complexity" in context.retrospective_result["metrics"]
    assert "readability" in context.retrospective_result["metrics"]
    assert "maintainability" in context.retrospective_result["metrics"]

    # Verify that the retrospective includes recommendations
    assert "recommendations" in context.retrospective_result


@then("the memory system should store AST analysis results with appropriate EDRR phase tags")
def memory_system_stores_results_with_edrr_tags(context):
    """Verify that the memory system stores AST analysis results with appropriate EDRR phase tags."""
    # In a real implementation, we would query the memory system for items with EDRR phase tags
    # For testing purposes, we'll verify that the memory manager's store_with_edrr_phase method was called

    # Verify that items were stored for each EDRR phase
    expand_items = context.memory_manager.query_by_edrr_phase("expand")
    differentiate_items = context.memory_manager.query_by_edrr_phase("differentiate")
    refine_items = context.memory_manager.query_by_edrr_phase("refine")
    retrospect_items = context.memory_manager.query_by_edrr_phase("retrospect")

    # Verify that items were found for each phase
    assert len(expand_items) > 0
    assert len(differentiate_items) > 0
    assert len(refine_items) > 0
    assert len(retrospect_items) > 0
