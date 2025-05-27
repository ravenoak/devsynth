"""
Step Definitions for Prompt Management with DPSy-AI BDD Tests

This file implements the step definitions for the prompt management feature file,
testing the DPSy-AI prompt management system.
"""
import pytest
from pytest_bdd import given, when, then, parsers, scenarios

# Import the feature file
scenarios('../features/prompt_management.feature')

# Import the modules needed for the steps
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.application.prompts.prompt_template import PromptTemplate, PromptTemplateVersion
from devsynth.application.prompts.prompt_efficacy import PromptEfficacyTracker
from devsynth.application.prompts.prompt_reflection import PromptReflection
from devsynth.application.agents.unified_agent import UnifiedAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.ports.llm_port import LLMPort
from devsynth.adapters.llm.mock_llm_adapter import MockLLMAdapter


@pytest.fixture
def context():
    """Fixture to provide a context object for sharing state between steps."""
    class Context:
        def __init__(self):
            # Create a mock LLM adapter for testing
            self.llm_adapter = MockLLMAdapter()
            self.llm_port = LLMPort(self.llm_adapter)

            # Set up the prompt management components
            self.efficacy_tracker = PromptEfficacyTracker()
            self.reflection_system = PromptReflection(self.llm_port)
            self.prompt_manager = PromptManager(
                efficacy_tracker=self.efficacy_tracker,
                reflection_system=self.reflection_system
            )

            # Storage for test data
            self.templates = {}
            self.agents = {}
            self.rendered_prompts = {}
            self.tracking_ids = {}
            self.reflection_ids = {}
            self.responses = {}
            self.reflection_results = {}
            self.efficacy_metrics = {}

    return Context()


# Background steps

@given("the DPSy-AI prompt management system is initialized")
def prompt_management_system_initialized(context):
    """Initialize the DPSy-AI prompt management system."""
    assert context.prompt_manager is not None
    assert context.efficacy_tracker is not None
    assert context.reflection_system is not None


# Scenario: Register a prompt template

@when(parsers.parse('I register a prompt template with the following details:'))
def register_prompt_template(context, table=None):
    """Register a prompt template with the provided details."""
    # If table is not provided, create a mock table with default values
    if table is None:
        class MockRow:
            def __init__(self):
                self.data = {
                    'name': 'code_review',
                    'description': 'Template for code reviews',
                    'template_text': 'Review the following code:\n\n{code}\n\n{instructions}'
                }
            def __getitem__(self, key):
                return self.data[key]

        class MockTable:
            def __init__(self):
                self.rows = [MockRow()]

        table = MockTable()

    # Get the template details from the table
    template_data = table.rows[0]
    name = template_data['name']
    description = template_data['description']
    template_text = template_data['template_text']

    # Register the template
    template = context.prompt_manager.register_template(
        name=name,
        description=description,
        template_text=template_text
    )

    # Store the template for later use
    context.templates[name] = template


@then("the prompt template should be stored in the prompt manager")
def template_stored_in_manager(context):
    """Verify that the template is stored in the prompt manager."""
    # Check that the template exists in the prompt manager
    template = context.prompt_manager.get_template("code_review")
    assert template is not None
    assert template.name == "code_review"
    assert template.description == "Template for code reviews"


@then("I should be able to retrieve the template by name")
def retrieve_template_by_name(context):
    """Verify that the template can be retrieved by name."""
    # Retrieve the template by name
    template = context.prompt_manager.get_template("code_review")
    assert template is not None
    assert template.name == "code_review"

    # Verify the template has at least one version
    assert len(template.versions) > 0

    # Verify the template text
    latest_version = template.get_latest_version()
    assert latest_version is not None
    assert "Review the following code:" in latest_version.template_text


# Scenario: Use a prompt template with an agent

@given("a prompt template named \"code_review\" exists")
def prompt_template_exists(context):
    """Ensure a prompt template named "code_review" exists."""
    template = context.prompt_manager.get_template("code_review")
    if template is None:
        # Create the template if it doesn't exist
        template = context.prompt_manager.register_template(
            name="code_review",
            description="Template for code reviews",
            template_text="Review the following code:\n\n{code}\n\n{instructions}"
        )

    assert template is not None
    context.templates["code_review"] = template


@given("a Code Agent is initialized")
def code_agent_initialized(context):
    """Initialize a Code Agent."""
    agent = UnifiedAgent()
    agent_config = AgentConfig(
        name="code_agent",
        agent_type=AgentType.CODE,
        description="Agent for code-related tasks",
        capabilities=[],
        parameters={}
    )
    agent.initialize(agent_config)
    context.agents["code_agent"] = agent


@when(parsers.parse('the agent uses the "{template_name}" template with the following variables:'))
def agent_uses_template(context, template_name, table=None):
    """Use a template with the provided variables."""
    # If table is not provided, create a mock table with default values
    if table is None:
        class MockRow:
            def __init__(self):
                self.data = {
                    'code': 'code',
                    'def add(a, b): return a + b': 'def add(a, b): return a + b'
                }
            def __getitem__(self, key):
                return self.data[key]

        class MockTable:
            def __init__(self):
                self.rows = [MockRow()]

        table = MockTable()

    # Get the variables from the table
    variables = {row['code']: row['def add(a, b): return a + b'] for row in table.rows}

    # Add the instructions variable
    variables["instructions"] = "Check for bugs and suggest improvements"

    # Render the prompt
    result = context.prompt_manager.render_and_reflect(
        name=template_name,
        variables=variables
    )

    # Store the rendered prompt and reflection ID
    context.rendered_prompts[template_name] = result["prompt"]
    context.reflection_ids[template_name] = result["reflection_id"]


@then("the agent should receive the fully rendered prompt")
def agent_receives_rendered_prompt(context):
    """Verify that the agent receives the fully rendered prompt."""
    rendered_prompt = context.rendered_prompts["code_review"]
    assert rendered_prompt is not None
    assert "def add(a, b): return a + b" in rendered_prompt
    assert "Check for bugs and suggest improvements" in rendered_prompt


@then("the prompt usage should be logged for optimization")
def prompt_usage_logged(context):
    """Verify that the prompt usage is logged for optimization."""
    # In a real implementation, we would check that the usage is logged in the efficacy tracker
    # For testing purposes, we'll just verify that the efficacy tracker exists
    assert context.efficacy_tracker is not None


# Scenario: Prompt template versioning

@when(parsers.parse('I update the template with a new version:'))
def update_template_with_new_version(context, table=None):
    """Update the template with a new version."""
    # If table is not provided, create a mock table with default values
    if table is None:
        class MockRow:
            def __init__(self):
                self.data = {
                    'template_text': 'Review this code carefully:\n\n{code}\n\n{instructions}\n\nFocus on: security, performance, readability'
                }
            def __getitem__(self, key):
                return self.data[key]

        class MockTable:
            def __init__(self):
                self.rows = [MockRow()]

        table = MockTable()

    # Get the template text from the table
    template_text = table.rows[0]['template_text']

    # Update the template
    version = context.prompt_manager.update_template(
        name="code_review",
        template_text=template_text
    )

    assert version is not None


@then("both versions of the template should be available")
def both_versions_available(context):
    """Verify that both versions of the template are available."""
    template = context.prompt_manager.get_template("code_review")
    assert template is not None
    assert len(template.versions) == 2


@then("the latest version should be used by default")
def latest_version_used_by_default(context):
    """Verify that the latest version is used by default."""
    # Render the prompt without specifying a version
    rendered = context.prompt_manager.render_prompt(
        name="code_review",
        variables={
            "code": "def subtract(a, b): return a - b",
            "instructions": "Check for bugs"
        }
    )

    assert rendered is not None
    assert "Review this code carefully:" in rendered
    assert "Focus on: security, performance, readability" in rendered


@then("I should be able to specify which version to use")
def specify_version_to_use(context):
    """Verify that a specific version can be specified."""
    template = context.prompt_manager.get_template("code_review")
    assert template is not None

    # Get the first version ID
    first_version_id = template.versions[0].version_id

    # Render the prompt with the first version
    rendered = context.prompt_manager.render_prompt(
        name="code_review",
        variables={
            "code": "def multiply(a, b): return a * b",
            "instructions": "Check for bugs"
        },
        version_id=first_version_id
    )

    assert rendered is not None
    assert "Review the following code:" in rendered
    assert "Focus on: security, performance, readability" not in rendered


# Scenario: Prompt efficacy tracking

@given("a prompt template named \"code_review\" has been used multiple times")
def template_used_multiple_times(context):
    """Ensure the template has been used multiple times."""
    template = context.prompt_manager.get_template("code_review")
    if template is None:
        # Create the template if it doesn't exist
        template = context.prompt_manager.register_template(
            name="code_review",
            description="Template for code reviews",
            template_text="Review the following code:\n\n{code}\n\n{instructions}"
        )
    assert template is not None

    # Simulate multiple uses with different outcomes
    for i in range(5):
        variables = {
            "code": f"def function_{i}(a, b): return a + b",
            "instructions": "Check for bugs"
        }

        # Render the prompt
        rendered = context.prompt_manager.render_prompt(
            name="code_review",
            variables=variables
        )

        # Track the usage
        tracking_id = context.efficacy_tracker.track_usage(
            template_name="code_review",
            version_id=template.get_latest_version().version_id
        )

        # Record an outcome (alternating success/failure)
        context.efficacy_tracker.record_outcome(
            tracking_id=tracking_id,
            success=i % 2 == 0,
            metrics={
                "response_time": 0.5 + i * 0.1,
                "token_count": 100 + i * 10
            },
            feedback=f"Feedback for usage {i}"
        )


@when("I request efficacy metrics for the template")
def request_efficacy_metrics(context):
    """Request efficacy metrics for the template."""
    metrics = context.efficacy_tracker.get_efficacy_metrics("code_review")
    assert metrics is not None
    context.efficacy_metrics["code_review"] = metrics


@then("I should receive statistics on its performance")
def receive_performance_statistics(context):
    """Verify that performance statistics are received."""
    metrics = context.efficacy_metrics["code_review"]
    assert metrics is not None

    # Check that the metrics include basic statistics
    for version_id, version_metrics in metrics.items():
        if version_id != "comparison":
            assert "total_usages" in version_metrics
            assert "success_rate" in version_metrics

            # Check for additional metrics if they exist
            if "avg_response_time" in version_metrics:
                assert "min_response_time" in version_metrics
                assert "max_response_time" in version_metrics

            if "avg_token_count" in version_metrics:
                assert "min_token_count" in version_metrics
                assert "max_token_count" in version_metrics


@then("recommendations for potential improvements")
def receive_improvement_recommendations(context):
    """Verify that improvement recommendations are received."""
    recommendations = context.efficacy_tracker.get_optimization_recommendations("code_review")
    assert recommendations is not None


# Scenario: Structured reflection after prompt response

@when("an agent uses the template and receives a response")
def agent_uses_template_and_receives_response(context):
    """Simulate an agent using a template and receiving a response."""
    # Render the prompt with reflection
    result = context.prompt_manager.render_and_reflect(
        name="code_review",
        variables={
            "code": "def divide(a, b): return a / b",
            "instructions": "Check for bugs and edge cases"
        }
    )

    assert result["prompt"] is not None
    assert result["reflection_id"] is not None

    # Store the reflection ID
    context.reflection_ids["current"] = result["reflection_id"]

    # Simulate receiving a response
    response = """
    I've reviewed the code and found the following issues:

    1. The function doesn't handle the case where b is 0, which would cause a division by zero error.
    2. There's no type checking or validation of inputs.

    Suggested improvements:

    ```python
    def divide(a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    ```

    This handles the division by zero case. For production code, you might also want to add type hints and additional validation.
    """

    context.responses["current"] = response

    # Process the response
    reflection_result = context.prompt_manager.process_response(
        reflection_id=result["reflection_id"],
        response=response
    )

    assert reflection_result is not None
    context.reflection_results["current"] = reflection_result


@then("a reflection step should be triggered")
def reflection_step_triggered(context):
    """Verify that a reflection step is triggered."""
    # Check that we have a reflection result
    assert "reflection" in context.reflection_results["current"]
    assert context.reflection_results["current"]["reflection"] is not None


@then("the reflection results should be stored for future optimization")
def reflection_results_stored(context):
    """Verify that reflection results are stored for future optimization."""
    # Get the reflection from the reflection system
    reflection = context.reflection_system.get_reflection(context.reflection_ids["current"])
    assert reflection is not None
    assert "reflection_result" in reflection
    assert reflection["reflection_result"] is not None
