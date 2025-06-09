import pytest
from pytest_bdd import given, when, then, parsers, scenarios
from unittest.mock import MagicMock, patch
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.agents.base import BaseAgent

# Import the feature file
scenarios('../features/multi_disciplinary_dialectical_reasoning.feature')

# Define a fixture for the context
@pytest.fixture
def context():
    class Context:
        def __init__(self):
            self.team = None
            self.task = None
            self.solution = None
            self.knowledge_sources = None
            self.disciplinary_agents = []
            self.result = None
    return Context()

# Helper function to create a mock agent with expertise
def create_mock_agent(name, expertise):
    agent = MagicMock(spec=BaseAgent)
    agent.name = name
    agent.agent_type = "mock"
    agent.current_role = None
    agent.expertise = expertise
    agent.has_been_primus = False
    return agent

# Background steps
@given("the DevSynth system is initialized")
def devsynth_initialized(context):
    """Ensure the context object for WSDE reasoning exists."""
    assert context is not None

@given("a WSDE team is created with multiple disciplinary agents")
def wsde_team_created(context):
    context.team = WSDETeam()

    # Create agents with different disciplinary expertise
    code_agent = create_mock_agent("CodeAgent", ["python", "coding"])
    security_agent = create_mock_agent("SecurityAgent", ["security", "authentication"])
    ux_agent = create_mock_agent("UXAgent", ["user_experience", "interface_design"])
    performance_agent = create_mock_agent("PerformanceAgent", ["performance", "optimization"])
    accessibility_agent = create_mock_agent("AccessibilityAgent", ["accessibility", "inclusive_design"])
    critic_agent = create_mock_agent("CriticAgent", ["dialectical_reasoning", "critique", "synthesis"])

    # Add agents to the team
    context.team.add_agent(code_agent)
    context.team.add_agent(security_agent)
    context.team.add_agent(ux_agent)
    context.team.add_agent(performance_agent)
    context.team.add_agent(accessibility_agent)
    context.team.add_agent(critic_agent)

    # Store agents for later use
    context.code_agent = code_agent
    context.security_agent = security_agent
    context.ux_agent = ux_agent
    context.performance_agent = performance_agent
    context.accessibility_agent = accessibility_agent
    context.critic_agent = critic_agent

# Scenario steps
@given("a task requiring multiple disciplinary perspectives")
def task_requiring_multiple_perspectives(context):
    context.task = {
        "type": "implementation_task", 
        "description": "Implement a user authentication system with a focus on security, usability, performance, and accessibility"
    }

@given("a proposed solution for the task")
def proposed_solution(context):
    context.solution = {
        "agent": "CodeAgent",
        "content": "Implement authentication using username/password with JWT tokens",
        "code": """
def authenticate(username, password):
    if username == 'admin' and password == 'password':
        token = generate_jwt_token(username)
        return token
    return None

def generate_jwt_token(username):
    # Generate a JWT token
    return "jwt_token_placeholder"
        """
    }

    # Add the solution to the team
    context.team.add_solution(context.task, context.solution)

@given("knowledge sources from multiple disciplines")
def knowledge_sources_multiple_disciplines(context):
    context.knowledge_sources = {
        "security": {
            "authentication_best_practices": [
                "Use multi-factor authentication for sensitive operations",
                "Store passwords using strong, adaptive hashing algorithms (e.g., bcrypt, Argon2)",
                "Implement rate limiting to prevent brute force attacks",
                "Use HTTPS for all authentication requests",
                "Set secure and HttpOnly flags on authentication cookies"
            ]
        },
        "user_experience": {
            "authentication_ux_principles": [
                "Minimize friction in the authentication process",
                "Provide clear error messages for failed authentication attempts",
                "Offer password recovery options",
                "Remember user preferences where appropriate",
                "Support single sign-on where possible"
            ]
        },
        "performance": {
            "authentication_performance_considerations": [
                "Optimize token validation for minimal latency",
                "Cache frequently used authentication data",
                "Use asynchronous processing for non-critical authentication tasks",
                "Implement efficient database queries for user lookup",
                "Monitor and optimize authentication service response times"
            ]
        },
        "accessibility": {
            "authentication_accessibility_guidelines": [
                "Ensure all authentication forms are keyboard navigable",
                "Provide appropriate ARIA labels for authentication form elements",
                "Support screen readers for error messages and instructions",
                "Maintain sufficient color contrast for text and interactive elements",
                "Allow authentication timeout extensions for users who need more time"
            ]
        }
    }

    # Set disciplinary agents
    context.disciplinary_agents = [
        context.security_agent,
        context.ux_agent,
        context.performance_agent,
        context.accessibility_agent
    ]

@given("a task requiring security and user experience considerations")
def task_requiring_security_and_ux(context):
    context.task = {
        "type": "implementation_task", 
        "description": "Implement a user authentication system with a focus on security and usability"
    }

@given("knowledge sources for security and user experience")
def knowledge_sources_security_and_ux(context):
    context.knowledge_sources = {
        "security": {
            "authentication_best_practices": [
                "Use multi-factor authentication for sensitive operations",
                "Store passwords using strong, adaptive hashing algorithms (e.g., bcrypt, Argon2)",
                "Implement rate limiting to prevent brute force attacks",
                "Use HTTPS for all authentication requests",
                "Set secure and HttpOnly flags on authentication cookies"
            ]
        },
        "user_experience": {
            "authentication_ux_principles": [
                "Minimize friction in the authentication process",
                "Provide clear error messages for failed authentication attempts",
                "Offer password recovery options",
                "Remember user preferences where appropriate",
                "Support single sign-on where possible"
            ]
        }
    }

    # Set disciplinary agents
    context.disciplinary_agents = [
        context.security_agent,
        context.ux_agent
    ]

@given("a task requiring performance and accessibility considerations")
def task_requiring_performance_and_accessibility(context):
    context.task = {
        "type": "implementation_task", 
        "description": "Implement a user authentication system with a focus on performance and accessibility"
    }

@given("knowledge sources for performance and accessibility")
def knowledge_sources_performance_and_accessibility(context):
    context.knowledge_sources = {
        "performance": {
            "authentication_performance_considerations": [
                "Optimize token validation for minimal latency",
                "Cache frequently used authentication data",
                "Use asynchronous processing for non-critical authentication tasks",
                "Implement efficient database queries for user lookup",
                "Monitor and optimize authentication service response times"
            ]
        },
        "accessibility": {
            "authentication_accessibility_guidelines": [
                "Ensure all authentication forms are keyboard navigable",
                "Provide appropriate ARIA labels for authentication form elements",
                "Support screen readers for error messages and instructions",
                "Maintain sufficient color contrast for text and interactive elements",
                "Allow authentication timeout extensions for users who need more time"
            ]
        }
    }

    # Set disciplinary agents
    context.disciplinary_agents = [
        context.performance_agent,
        context.accessibility_agent
    ]

@given("a task requiring security, user experience, performance, and accessibility considerations")
def task_requiring_all_four_disciplines(context):
    context.task = {
        "type": "implementation_task", 
        "description": "Implement a comprehensive user authentication system with a focus on security, usability, performance, and accessibility"
    }

@given("knowledge sources for all four disciplines")
def knowledge_sources_all_four_disciplines(context):
    context.knowledge_sources = {
        "security": {
            "authentication_best_practices": [
                "Use multi-factor authentication for sensitive operations",
                "Store passwords using strong, adaptive hashing algorithms (e.g., bcrypt, Argon2)",
                "Implement rate limiting to prevent brute force attacks",
                "Use HTTPS for all authentication requests",
                "Set secure and HttpOnly flags on authentication cookies"
            ]
        },
        "user_experience": {
            "authentication_ux_principles": [
                "Minimize friction in the authentication process",
                "Provide clear error messages for failed authentication attempts",
                "Offer password recovery options",
                "Remember user preferences where appropriate",
                "Support single sign-on where possible"
            ]
        },
        "performance": {
            "authentication_performance_considerations": [
                "Optimize token validation for minimal latency",
                "Cache frequently used authentication data",
                "Use asynchronous processing for non-critical authentication tasks",
                "Implement efficient database queries for user lookup",
                "Monitor and optimize authentication service response times"
            ]
        },
        "accessibility": {
            "authentication_accessibility_guidelines": [
                "Ensure all authentication forms are keyboard navigable",
                "Provide appropriate ARIA labels for authentication form elements",
                "Support screen readers for error messages and instructions",
                "Maintain sufficient color contrast for text and interactive elements",
                "Allow authentication timeout extensions for users who need more time"
            ]
        }
    }

    # Set disciplinary agents
    context.disciplinary_agents = [
        context.security_agent,
        context.ux_agent,
        context.performance_agent,
        context.accessibility_agent
    ]

@when("multi-disciplinary dialectical reasoning is applied")
def apply_multi_disciplinary_dialectical_reasoning(context):
    context.result = context.team.apply_multi_disciplinary_dialectical_reasoning(
        context.task,
        context.critic_agent,
        context.knowledge_sources,
        context.disciplinary_agents
    )

@then("the result should contain the original thesis")
def result_contains_thesis(context):
    assert "thesis" in context.result
    assert context.result["thesis"] is not None

@then("the result should contain perspectives from multiple disciplines")
def result_contains_multiple_perspectives(context):
    assert "disciplinary_perspectives" in context.result
    assert len(context.result["disciplinary_perspectives"]) >= 2

@then("the result should contain a synthesis that integrates multiple perspectives")
def result_contains_synthesis(context):
    assert "synthesis" in context.result
    assert "integrated_perspectives" in context.result["synthesis"]
    assert len(context.result["synthesis"]["integrated_perspectives"]) >= 2

@then("the result should contain an evaluation from multiple perspectives")
def result_contains_evaluation(context):
    assert "evaluation" in context.result
    assert "perspective_scores" in context.result["evaluation"]
    assert len(context.result["evaluation"]["perspective_scores"]) >= 2

@then("the synthesis should address conflicts between perspectives")
def synthesis_addresses_conflicts(context):
    assert "perspective_conflicts" in context.result["synthesis"]
    assert "conflict_resolutions" in context.result["synthesis"]

@then("the synthesis should be an improvement over the original solution")
def synthesis_is_improvement(context):
    assert context.result["synthesis"]["is_improvement"]
    assert "improved_solution" in context.result["synthesis"]

@then("the result should identify conflicts between security and user experience")
def result_identifies_security_ux_conflicts(context):
    assert "perspective_conflicts" in context.result["synthesis"]

    # Check if there's at least one conflict between security and user experience
    found_conflict = False
    for conflict in context.result["synthesis"]["perspective_conflicts"]:
        if "security" in conflict["disciplines"] and "user_experience" in conflict["disciplines"]:
            found_conflict = True
            break

    assert found_conflict

@then("the synthesis should resolve conflicts between security and user experience")
def synthesis_resolves_security_ux_conflicts(context):
    assert "conflict_resolutions" in context.result["synthesis"]

    # Check if there's at least one resolution for security and user experience
    found_resolution = False
    for resolution in context.result["synthesis"]["conflict_resolutions"]:
        if "security" in resolution["disciplines"] and "user_experience" in resolution["disciplines"]:
            found_resolution = True
            break

    assert found_resolution

@then("the evaluation should assess the solution from both security and user experience perspectives")
def evaluation_assesses_security_and_ux(context):
    assert "perspective_scores" in context.result["evaluation"]

    # Check if there are scores for both security and user experience
    perspective_disciplines = [p["discipline"] for p in context.result["evaluation"]["perspective_scores"]]
    assert "security" in perspective_disciplines
    assert "user_experience" in perspective_disciplines

@then("the result should identify conflicts between performance and accessibility")
def result_identifies_performance_accessibility_conflicts(context):
    assert "perspective_conflicts" in context.result["synthesis"]

    # Check if there's at least one conflict between performance and accessibility
    found_conflict = False
    for conflict in context.result["synthesis"]["perspective_conflicts"]:
        if "performance" in conflict["disciplines"] and "accessibility" in conflict["disciplines"]:
            found_conflict = True
            break

    assert found_conflict

@then("the synthesis should resolve conflicts between performance and accessibility")
def synthesis_resolves_performance_accessibility_conflicts(context):
    assert "conflict_resolutions" in context.result["synthesis"]

    # Check if there's at least one resolution for performance and accessibility
    found_resolution = False
    for resolution in context.result["synthesis"]["conflict_resolutions"]:
        if "performance" in resolution["disciplines"] and "accessibility" in resolution["disciplines"]:
            found_resolution = True
            break

    assert found_resolution

@then("the evaluation should assess the solution from both performance and accessibility perspectives")
def evaluation_assesses_performance_and_accessibility(context):
    assert "perspective_scores" in context.result["evaluation"]

    # Check if there are scores for both performance and accessibility
    perspective_disciplines = [p["discipline"] for p in context.result["evaluation"]["perspective_scores"]]
    assert "performance" in perspective_disciplines
    assert "accessibility" in perspective_disciplines

@then("the result should contain perspectives from all four disciplines")
def result_contains_all_four_perspectives(context):
    assert "disciplinary_perspectives" in context.result

    # Check if there are perspectives for all four disciplines
    perspective_disciplines = [p["discipline"] for p in context.result["disciplinary_perspectives"]]
    assert "security" in perspective_disciplines
    assert "user_experience" in perspective_disciplines
    assert "performance" in perspective_disciplines
    assert "accessibility" in perspective_disciplines

@then("the synthesis should integrate recommendations from all four disciplines")
def synthesis_integrates_all_four_disciplines(context):
    assert "integrated_perspectives" in context.result["synthesis"]

    # Check if there are integrated perspectives for all four disciplines
    integrated_disciplines = [p["discipline"] for p in context.result["synthesis"]["integrated_perspectives"]]
    assert "security" in integrated_disciplines
    assert "user_experience" in integrated_disciplines
    assert "performance" in integrated_disciplines
    assert "accessibility" in integrated_disciplines

@then("the evaluation should assess the solution from all four perspectives")
def evaluation_assesses_all_four_perspectives(context):
    assert "perspective_scores" in context.result["evaluation"]

    # Check if there are scores for all four disciplines
    perspective_disciplines = [p["discipline"] for p in context.result["evaluation"]["perspective_scores"]]
    assert "security" in perspective_disciplines
    assert "user_experience" in perspective_disciplines
    assert "performance" in perspective_disciplines
    assert "accessibility" in perspective_disciplines

@then("the overall assessment should reflect the balance of all perspectives")
def overall_assessment_reflects_balance(context):
    assert "overall_assessment" in context.result["evaluation"]
    assert "balance" in context.result["evaluation"]["overall_assessment"].lower()
