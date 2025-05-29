"""
Step Definitions for Enhanced Dialectical Reasoning BDD Tests

This file implements the step definitions for the enhanced dialectical reasoning
feature file, testing the advanced dialectical reasoning capabilities of the WSDE model.
"""
import pytest
from pytest_bdd import given, when, then, parsers, scenarios

# Import the feature file
scenarios('../features/enhanced_dialectical_reasoning.feature')

# Import the modules needed for the steps
from devsynth.domain.models.wsde import WSDETeam
from devsynth.adapters.agents.agent_adapter import WSDETeamCoordinator
from devsynth.application.agents.unified_agent import UnifiedAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from typing import Dict, List, Any


@pytest.fixture
def context():
    """Fixture to provide a context object for sharing state between steps."""
    class Context:
        def __init__(self):
            self.team_coordinator = WSDETeamCoordinator()
            self.agents = {}
            self.teams = {}
            self.tasks = {}
            self.solutions = {}
            self.current_team_id = None
            self.dialectical_result = None

    return Context()


# Background steps

@given("the DevSynth system is initialized")
def devsynth_system_initialized(context):
    """Initialize the DevSynth system."""
    # The system is initialized by creating the team coordinator
    assert context.team_coordinator is not None


@given("a team of agents is configured")
def team_of_agents_configured(context):
    """Configure a team of agents."""
    # Create a default team
    team_id = "test_team"
    context.team_coordinator.create_team(team_id)
    context.current_team_id = team_id
    context.teams[team_id] = context.team_coordinator.get_team(team_id)


@given("the WSDE model is enabled")
def wsde_model_enabled(context):
    """Enable the WSDE model."""
    # The WSDE model is enabled by default when a team is created
    assert context.teams[context.current_team_id] is not None


@given("a Critic agent with dialectical reasoning expertise is added to the team")
def critic_agent_added(context):
    """Add a Critic agent with dialectical reasoning expertise to the team."""
    # Create a Critic agent
    agent = UnifiedAgent()
    agent_config = AgentConfig(
        name="critic_agent",
        agent_type=AgentType.ORCHESTRATOR,
        description="Agent for applying enhanced dialectical reasoning",
        capabilities=[],
        parameters={"expertise": ["dialectical_reasoning", "critique", "synthesis", "evaluation"]}
    )
    agent.initialize(agent_config)
    context.agents["critic_agent"] = agent
    context.team_coordinator.add_agent(agent)


# Scenario: Multi-stage dialectical reasoning process

@when("a solution is proposed for a complex task")
def solution_proposed_for_complex_task(context):
    """Propose a solution for a complex task."""
    # Create a complex task
    task = {
        "id": "complex_task_1",
        "type": "implementation_task",
        "description": "Implement a secure user authentication system with multi-factor authentication"
    }
    context.tasks["complex_task"] = task

    # Create a proposed solution
    solution = {
        "agent": "code_agent",
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
    team = context.teams[context.current_team_id]
    team.add_solution(task, solution)


@then("the Critic agent should apply multi-stage dialectical reasoning")
def critic_applies_multi_stage_reasoning(context):
    """Verify that the Critic agent applies multi-stage dialectical reasoning."""
    # Apply dialectical reasoning to the task
    team = context.teams[context.current_team_id]
    critic_agent = context.agents["critic_agent"]
    task = context.tasks["complex_task"]

    # Apply enhanced dialectical reasoning
    context.dialectical_result = team.apply_enhanced_dialectical_reasoning(task, critic_agent)

    # Verify that the result contains all stages
    assert "thesis" in context.dialectical_result
    assert "antithesis" in context.dialectical_result
    assert "synthesis" in context.dialectical_result
    assert "evaluation" in context.dialectical_result


@then("the reasoning should include thesis identification")
def reasoning_includes_thesis_identification(context):
    """Verify that the reasoning includes thesis identification."""
    # Verify that the thesis is properly identified
    assert "thesis" in context.dialectical_result
    assert "identification" in context.dialectical_result["thesis"]
    assert "key_points" in context.dialectical_result["thesis"]
    assert len(context.dialectical_result["thesis"]["key_points"]) > 0


@then("the reasoning should include antithesis generation with multiple critique categories")
def reasoning_includes_antithesis_with_categories(context):
    """Verify that the reasoning includes antithesis generation with multiple critique categories."""
    # Verify that the antithesis includes multiple critique categories
    assert "antithesis" in context.dialectical_result
    assert "critique_categories" in context.dialectical_result["antithesis"]
    assert len(context.dialectical_result["antithesis"]["critique_categories"]) >= 3


@then("the reasoning should include synthesis creation that addresses all critiques")
def reasoning_includes_synthesis_addressing_all_critiques(context):
    """Verify that the reasoning includes synthesis creation that addresses all critiques."""
    # Verify that the synthesis addresses all critiques
    assert "synthesis" in context.dialectical_result
    assert "addressed_critiques" in context.dialectical_result["synthesis"]

    # All critiques should be addressed
    antithesis_categories = context.dialectical_result["antithesis"]["critique_categories"]
    addressed_critiques = context.dialectical_result["synthesis"]["addressed_critiques"]

    for category in antithesis_categories:
        assert category in addressed_critiques


@then("the reasoning should include a final evaluation of the synthesis")
def reasoning_includes_final_evaluation(context):
    """Verify that the reasoning includes a final evaluation of the synthesis."""
    # Verify that the result includes a final evaluation
    assert "evaluation" in context.dialectical_result
    assert "strengths" in context.dialectical_result["evaluation"]
    assert "weaknesses" in context.dialectical_result["evaluation"]
    assert "overall_assessment" in context.dialectical_result["evaluation"]


# Scenario: Comprehensive critique categories

@then("the Critic agent should analyze the solution across multiple dimensions")
def critic_analyzes_multiple_dimensions(context):
    """Verify that the Critic agent analyzes the solution across multiple dimensions."""
    # Apply dialectical reasoning if not already done
    if context.dialectical_result is None:
        team = context.teams[context.current_team_id]
        critic_agent = context.agents["critic_agent"]
        task = context.tasks["complex_task"]
        context.dialectical_result = team.apply_enhanced_dialectical_reasoning(task, critic_agent)

    # Verify that the antithesis includes multiple dimensions
    assert "antithesis" in context.dialectical_result
    assert "critique_categories" in context.dialectical_result["antithesis"]
    assert len(context.dialectical_result["antithesis"]["critique_categories"]) >= 5


@then("the critique should include security considerations")
def critique_includes_security(context):
    """Verify that the critique includes security considerations."""
    # Verify that security is one of the critique categories
    assert "security" in context.dialectical_result["antithesis"]["critique_categories"]


@then("the critique should include performance considerations")
def critique_includes_performance(context):
    """Verify that the critique includes performance considerations."""
    # Verify that performance is one of the critique categories
    assert "performance" in context.dialectical_result["antithesis"]["critique_categories"]


@then("the critique should include maintainability considerations")
def critique_includes_maintainability(context):
    """Verify that the critique includes maintainability considerations."""
    # Verify that maintainability is one of the critique categories
    assert "maintainability" in context.dialectical_result["antithesis"]["critique_categories"]


@then("the critique should include usability considerations")
def critique_includes_usability(context):
    """Verify that the critique includes usability considerations."""
    # Verify that usability is one of the critique categories
    assert "usability" in context.dialectical_result["antithesis"]["critique_categories"]


@then("the critique should include testability considerations")
def critique_includes_testability(context):
    """Verify that the critique includes testability considerations."""
    # Verify that testability is one of the critique categories
    assert "testability" in context.dialectical_result["antithesis"]["critique_categories"]


# Scenario: Dialectical reasoning with multiple solutions

@given("multiple solutions are proposed for a task")
def multiple_solutions_proposed(context):
    """Propose multiple solutions for a task."""
    # Create a task
    task = {
        "id": "multi_solution_task",
        "type": "implementation_task",
        "description": "Implement a data caching mechanism for API responses"
    }
    context.tasks["multi_solution_task"] = task

    # Create multiple solutions
    solution1 = {
        "agent": "code_agent_1",
        "content": "Implement in-memory caching using a dictionary with TTL",
        "code": """
def get_cached_data(key, ttl=300):
    if key in cache and time.time() - cache[key]['timestamp'] < ttl:
        return cache[key]['data']
    data = fetch_from_api(key)
    cache[key] = {'data': data, 'timestamp': time.time()}
    return data
        """
    }

    solution2 = {
        "agent": "code_agent_2",
        "content": "Implement Redis-based caching with automatic expiration",
        "code": """
def get_cached_data(key):
    data = redis_client.get(key)
    if data:
        return json.loads(data)
    data = fetch_from_api(key)
    redis_client.setex(key, 300, json.dumps(data))
    return data
        """
    }

    solution3 = {
        "agent": "code_agent_3",
        "content": "Implement file-based caching with JSON serialization",
        "code": """
def get_cached_data(key):
    cache_file = f"cache/{key}.json"
    if os.path.exists(cache_file) and time.time() - os.path.getmtime(cache_file) < 300:
        with open(cache_file, 'r') as f:
            return json.load(f)
    data = fetch_from_api(key)
    os.makedirs("cache", exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(data, f)
    return data
        """
    }

    # Add the solutions to the team
    team = context.teams[context.current_team_id]
    team.add_solution(task, solution1)
    team.add_solution(task, solution2)
    team.add_solution(task, solution3)


@when("dialectical reasoning is applied to compare the solutions")
def dialectical_reasoning_applied_to_compare(context):
    """Apply dialectical reasoning to compare the solutions."""
    # Apply dialectical reasoning to the task with multiple solutions
    team = context.teams[context.current_team_id]
    critic_agent = context.agents["critic_agent"]
    task = context.tasks["multi_solution_task"]

    # Apply enhanced dialectical reasoning with multiple solutions
    context.dialectical_result = team.apply_enhanced_dialectical_reasoning_multi(task, critic_agent)


@then("each solution should be analyzed as a potential thesis")
def each_solution_analyzed_as_thesis(context):
    """Verify that each solution is analyzed as a potential thesis."""
    # Verify that all solutions are analyzed
    assert "solution_analyses" in context.dialectical_result
    assert len(context.dialectical_result["solution_analyses"]) == 3


@then("comparative critiques should be generated")
def comparative_critiques_generated(context):
    """Verify that comparative critiques are generated."""
    # Verify that comparative critiques are generated
    assert "comparative_analysis" in context.dialectical_result
    assert "strengths_comparison" in context.dialectical_result["comparative_analysis"]
    assert "weaknesses_comparison" in context.dialectical_result["comparative_analysis"]
    assert "trade_offs" in context.dialectical_result["comparative_analysis"]


@then("a synthesized solution should incorporate the best elements of each proposal")
def synthesized_solution_incorporates_best_elements(context):
    """Verify that a synthesized solution incorporates the best elements of each proposal."""
    # Verify that the synthesis incorporates elements from multiple solutions
    assert "synthesis" in context.dialectical_result
    assert "incorporated_elements" in context.dialectical_result["synthesis"]
    assert len(context.dialectical_result["synthesis"]["incorporated_elements"]) >= 3


@then("the final solution should be superior to any individual proposal")
def final_solution_superior(context):
    """Verify that the final solution is superior to any individual proposal."""
    # Verify that the final solution is evaluated as superior
    assert "evaluation" in context.dialectical_result
    assert "comparative_assessment" in context.dialectical_result["evaluation"]
    assert context.dialectical_result["evaluation"]["comparative_assessment"] == "superior"


# Scenario: Dialectical reasoning with external knowledge integration

@given("external knowledge sources are available")
def external_knowledge_sources_available(context):
    """Set up external knowledge sources for the test."""
    # Create a dictionary of external knowledge sources
    context.external_knowledge = {
        "security_best_practices": {
            "authentication": [
                "Use multi-factor authentication for sensitive operations",
                "Store passwords using strong, adaptive hashing algorithms (e.g., bcrypt, Argon2)",
                "Implement rate limiting to prevent brute force attacks",
                "Use HTTPS for all authentication requests",
                "Set secure and HttpOnly flags on authentication cookies"
            ],
            "data_protection": [
                "Encrypt sensitive data at rest and in transit",
                "Implement proper access controls",
                "Follow the principle of least privilege",
                "Regularly audit access to sensitive data",
                "Have a data breach response plan"
            ]
        },
        "industry_standards": {
            "OWASP": [
                "OWASP Top 10 Web Application Security Risks",
                "OWASP Application Security Verification Standard (ASVS)",
                "OWASP Secure Coding Practices"
            ],
            "ISO": [
                "ISO/IEC 27001 - Information security management",
                "ISO/IEC 27002 - Code of practice for information security controls"
            ],
            "NIST": [
                "NIST Special Publication 800-53 - Security and Privacy Controls",
                "NIST Cybersecurity Framework"
            ]
        },
        "compliance_requirements": {
            "GDPR": [
                "Obtain explicit consent for data collection",
                "Provide mechanisms for users to access, modify, and delete their data",
                "Report data breaches within 72 hours",
                "Conduct Data Protection Impact Assessments (DPIA)"
            ],
            "HIPAA": [
                "Implement technical safeguards for PHI",
                "Conduct regular risk assessments",
                "Maintain audit trails of PHI access",
                "Have Business Associate Agreements (BAA) in place"
            ],
            "PCI-DSS": [
                "Maintain a secure network and systems",
                "Protect cardholder data",
                "Implement strong access control measures",
                "Regularly test security systems and processes"
            ]
        }
    }

    # Add the external knowledge to the team
    team = context.teams[context.current_team_id]
    team.external_knowledge = context.external_knowledge

# Reuse the existing step for the external knowledge scenario
@given("a solution is proposed for a complex task", target_fixture="solution_proposed")
def solution_proposed_for_external_knowledge(context):
    """Propose a solution for a complex task in the external knowledge scenario."""
    # Call the existing step implementation
    solution_proposed_for_complex_task(context)
    return context


@when("dialectical reasoning with external knowledge is applied")
def dialectical_reasoning_with_external_knowledge_applied(context):
    """Apply dialectical reasoning with external knowledge integration."""
    # Apply dialectical reasoning to the task with external knowledge
    team = context.teams[context.current_team_id]
    critic_agent = context.agents["critic_agent"]
    task = context.tasks["complex_task"]

    # Apply enhanced dialectical reasoning with external knowledge
    context.dialectical_result = team.apply_enhanced_dialectical_reasoning_with_knowledge(
        task, 
        critic_agent,
        context.external_knowledge
    )


@then("the reasoning should incorporate relevant external knowledge")
def reasoning_incorporates_external_knowledge(context):
    """Verify that the reasoning incorporates relevant external knowledge."""
    # Verify that the result includes external knowledge
    assert "external_knowledge" in context.dialectical_result
    assert len(context.dialectical_result["external_knowledge"]["relevant_sources"]) > 0


@then("the critique should reference industry best practices")
def critique_references_industry_best_practices(context):
    """Verify that the critique references industry best practices."""
    # Verify that the antithesis references industry best practices
    assert "antithesis" in context.dialectical_result
    assert "industry_references" in context.dialectical_result["antithesis"]
    assert len(context.dialectical_result["antithesis"]["industry_references"]) > 0


@then("the synthesis should align with external standards")
def synthesis_aligns_with_external_standards(context):
    """Verify that the synthesis aligns with external standards."""
    # Verify that the synthesis aligns with external standards
    assert "synthesis" in context.dialectical_result
    assert "standards_alignment" in context.dialectical_result["synthesis"]
    assert len(context.dialectical_result["synthesis"]["standards_alignment"]) > 0


@then("the evaluation should consider compliance with external requirements")
def evaluation_considers_compliance(context):
    """Verify that the evaluation considers compliance with external requirements."""
    # Verify that the evaluation considers compliance
    assert "evaluation" in context.dialectical_result
    assert "compliance_assessment" in context.dialectical_result["evaluation"]
    assert len(context.dialectical_result["evaluation"]["compliance_assessment"]) > 0
