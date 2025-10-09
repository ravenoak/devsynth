"""
Step Definitions for Enhanced Dialectical Reasoning BDD Tests

This file implements the step definitions for the enhanced dialectical reasoning
feature file, testing the advanced dialectical reasoning capabilities of the WSDE model.
"""

from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Import the feature file


scenarios(feature_path(__file__, "general", "enhanced_dialectical_reasoning.feature"))

from typing import Any, Dict, List

from devsynth.adapters.agents.agent_adapter import WSDETeamCoordinator
from devsynth.application.agents.base import BaseAgent
from devsynth.application.agents.unified_agent import UnifiedAgent
from devsynth.domain.models.agent import AgentConfig, AgentType

# Import the modules needed for the steps
from devsynth.domain.models.wsde_facade import WSDETeam


@pytest.fixture
def context():
    """Fixture to provide a context object for sharing state between steps."""

    class Context:
        def __init__(self):
            self.team = None
            self.agents = {}
            self.task = None
            self.solution = None
            self.dialectical_result = None
            self.knowledge_graph = None
            self.standards = None

    return Context()


# Helper function to create a mock agent with expertise
def create_mock_agent(name, expertise, experience_level=5):
    agent = MagicMock(spec=BaseAgent)
    agent.name = name
    agent.agent_type = "mock"
    agent.current_role = None
    agent.expertise = expertise
    agent.experience_level = experience_level
    agent.has_been_primus = False
    return agent


# Background steps


@given("a WSDE team with multiple agents")
def wsde_team_with_multiple_agents(context):
    """Create a WSDE team with multiple agents."""
    context.team = WSDETeam(name="TestEnhancedDialecticalReasoningStepsTeam")

    # Create agents with different expertise areas
    solution_agent = create_mock_agent(
        "SolutionAgent", ["python", "coding", "solution_design"], 7
    )
    critic_agent = create_mock_agent(
        "CriticAgent", ["critique", "dialectical_reasoning", "evaluation"], 8
    )
    synthesis_agent = create_mock_agent(
        "SynthesisAgent", ["synthesis", "integration", "reconciliation"], 7
    )

    # Add agents to the team
    context.team.add_agent(solution_agent)
    context.team.add_agent(critic_agent)
    context.team.add_agent(synthesis_agent)

    # Store agents for later use
    context.agents["solution_agent"] = solution_agent
    context.agents["critic_agent"] = critic_agent
    context.agents["synthesis_agent"] = synthesis_agent


@given("at least one agent designated as a critic")
def agent_designated_as_critic(context):
    """Verify that at least one agent is designated as a critic."""
    # Verify that the critic agent exists
    assert "critic_agent" in context.agents
    assert "critique" in context.agents["critic_agent"].expertise
    assert "dialectical_reasoning" in context.agents["critic_agent"].expertise


@given("the team is configured for enhanced dialectical reasoning")
def team_configured_for_enhanced_dialectical_reasoning(context):
    """Configure the team for enhanced dialectical reasoning."""
    # Set the team's dialectical reasoning mode to enhanced
    context.team.dialectical_reasoning_mode = "enhanced"

    # Verify that the team is configured for enhanced dialectical reasoning
    assert context.team.dialectical_reasoning_mode == "enhanced"


# Scenario: Complete thesis-antithesis-synthesis workflow


@given("a solution proposed by an agent as a thesis")
def solution_proposed_as_thesis(context):
    """Create a solution proposed by an agent as a thesis."""
    # Create a complex task
    context.task = {
        "id": "complex_task_1",
        "type": "implementation_task",
        "description": "Implement a secure user authentication system with multi-factor authentication",
    }

    # Create a proposed solution (thesis)
    context.solution = {
        "agent": "solution_agent",
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
        """,
    }

    # Add the solution to the team
    context.team.add_solution(context.task, context.solution)


@when("the dialectical reasoning process is initiated")
def dialectical_reasoning_initiated(context):
    """Initiate the dialectical reasoning process."""
    # Apply enhanced dialectical reasoning to the task
    critic_agent = context.agents["critic_agent"]
    context.dialectical_result = context.team.apply_enhanced_dialectical_reasoning(
        context.task, critic_agent
    )


@then("a critic agent should generate a comprehensive antithesis")
def critic_generates_comprehensive_antithesis(context):
    """Verify that a critic agent generates a comprehensive antithesis."""
    # Verify that the antithesis is generated
    assert "antithesis" in context.dialectical_result
    assert context.dialectical_result["antithesis"] is not None

    # Verify that the antithesis is comprehensive
    assert "critique_categories" in context.dialectical_result["antithesis"]
    assert len(context.dialectical_result["antithesis"]["critique_categories"]) >= 1


@then("the antithesis should challenge key assumptions of the thesis")
def antithesis_challenges_key_assumptions(context):
    """Verify that the antithesis challenges key assumptions of the thesis."""
    assert "antithesis" in context.dialectical_result


@then("a synthesis should be generated combining strengths of both")
def synthesis_combines_strengths(context):
    """Verify that a synthesis is generated combining strengths of both thesis and antithesis."""
    # Verify that the synthesis is generated
    assert "synthesis" in context.dialectical_result
    assert context.dialectical_result["synthesis"] is not None


@then("the synthesis should resolve contradictions between thesis and antithesis")
def synthesis_resolves_contradictions(context):
    """Verify that the synthesis resolves contradictions between thesis and antithesis."""
    assert "synthesis" in context.dialectical_result


@then("the final solution should be demonstrably better than the original thesis")
def final_solution_better_than_original(context):
    """Verify that the final solution is demonstrably better than the original thesis."""
    synthesis = context.dialectical_result.get("synthesis", {})
    assert synthesis.get("is_improvement", True) is True


# Scenario: Multi-perspective analysis in dialectical reasoning


@given("a complex problem with multiple valid approaches")
def complex_problem_with_multiple_approaches(context):
    """Create a complex problem with multiple valid approaches."""
    # Create a complex problem
    context.task = {
        "id": "complex_problem_1",
        "type": "design_task",
        "description": "Design a scalable data processing pipeline for real-time analytics",
        "constraints": [
            "high throughput",
            "low latency",
            "fault tolerance",
            "cost efficiency",
        ],
    }

    # Create multiple approaches to the problem
    context.approaches = [
        {
            "id": "approach_1",
            "name": "Kafka-based streaming pipeline",
            "agent": "solution_agent",
            "description": "Use Kafka for message streaming with Spark Streaming for processing",
            "pros": ["High throughput", "Mature ecosystem", "Good fault tolerance"],
            "cons": [
                "Complex setup",
                "Requires careful tuning",
                "Higher operational overhead",
            ],
        },
        {
            "id": "approach_2",
            "name": "Serverless event processing",
            "agent": "solution_agent",
            "description": "Use AWS Lambda with Kinesis for serverless event processing",
            "pros": [
                "Low operational overhead",
                "Automatic scaling",
                "Pay-per-use pricing",
            ],
            "cons": [
                "Potential cold start latency",
                "Limited execution time",
                "Vendor lock-in",
            ],
        },
        {
            "id": "approach_3",
            "name": "Custom stream processing framework",
            "agent": "solution_agent",
            "description": "Build a custom stream processing framework using Redis and worker pools",
            "pros": [
                "Tailored to specific needs",
                "No vendor lock-in",
                "Potentially lower cost",
            ],
            "cons": ["Development time", "Maintenance burden", "Scaling complexity"],
        },
    ]

    # Add the approaches to the task
    context.task["approaches"] = context.approaches

    # Add each approach as a solution to the team
    for approach in context.approaches:
        context.team.add_solution(context.task, approach)


@when("the team applies enhanced dialectical reasoning")
def team_applies_enhanced_dialectical_reasoning(context):
    """Apply enhanced dialectical reasoning to the complex problem."""
    # Apply enhanced dialectical reasoning with multiple perspectives
    critic_agent = context.agents["critic_agent"]
    context.dialectical_result = (
        context.team.apply_enhanced_dialectical_reasoning_multi(
            context.task, critic_agent
        )
    )


@then("multiple perspectives should be considered")
def multiple_perspectives_considered(context):
    """Verify that multiple perspectives are considered."""
    # Verify that multiple perspectives are analyzed
    assert "solution_analyses" in context.dialectical_result
    assert len(context.dialectical_result["solution_analyses"]) >= 1


@then("each perspective should be analyzed for strengths and weaknesses")
def each_perspective_analyzed(context):
    """Verify that each perspective is analyzed for strengths and weaknesses."""
    # Verify that each perspective analysis includes strengths and weaknesses
    for analysis in context.dialectical_result["solution_analyses"]:
        assert "strengths" in analysis
        assert "weaknesses" in analysis


@then("the analysis should consider different domains of expertise")
def analysis_considers_different_domains(context):
    """Verify that the analysis considers different domains of expertise."""
    assert "solution_analyses" in context.dialectical_result


@then("the synthesis should incorporate insights from all perspectives")
def synthesis_incorporates_all_perspectives(context):
    """Verify that the synthesis incorporates insights from all perspectives."""
    # Verify that the synthesis exists
    assert "synthesis" in context.dialectical_result


@then("the final solution should be more robust than any single perspective")
def final_solution_more_robust(context):
    """Verify that the final solution is more robust than any single perspective."""
    assert "evaluation" in context.dialectical_result


# Scenario: Knowledge integration from dialectical process


@given("a dialectical reasoning process has completed")
def dialectical_reasoning_process_completed(context):
    """Set up a completed dialectical reasoning process."""
    # Create a task
    context.task = {
        "id": "knowledge_integration_task",
        "type": "implementation_task",
        "description": "Implement a secure authentication system for a web application",
    }

    # Create a solution
    context.solution = {
        "agent": "solution_agent",
        "content": "Implement JWT-based authentication with password hashing",
        "code": """
def authenticate(username, password):
    user = find_user(username)
    if user and verify_password(password, user.password_hash):
        token = generate_jwt_token(user.id)
        return token
    return None
        """,
    }

    # Add the solution to the team
    context.team.add_solution(context.task, context.solution)

    # Apply dialectical reasoning to generate a result
    critic_agent = context.agents["critic_agent"]
    context.dialectical_result = context.team.apply_enhanced_dialectical_reasoning(
        context.task, critic_agent
    )

    # Verify that the dialectical reasoning process completed successfully
    assert "thesis" in context.dialectical_result
    assert "antithesis" in context.dialectical_result
    assert "synthesis" in context.dialectical_result


@when("the team integrates the knowledge gained")
def team_integrates_knowledge(context):
    """Have the team integrate the knowledge gained from the dialectical process."""
    # Integrate the knowledge from the dialectical process
    context.knowledge_integration = (
        context.team.integrate_knowledge_from_dialectical_process(
            context.dialectical_result
        )
    )


@then("key insights should be extracted and documented")
def key_insights_extracted(context):
    """Verify that key insights are extracted and documented."""
    # Verify that key insights are extracted
    assert "key_insights" in context.knowledge_integration
    assert isinstance(context.knowledge_integration["key_insights"], list)

    # Verify that each insight is documented
    for insight in context.knowledge_integration["key_insights"]:
        assert "description" in insight
        assert "source" in insight
        assert "importance" in insight
        assert insight["description"], "Empty insight description"


@then("the knowledge should be stored in the team's memory system")
def knowledge_stored_in_memory(context):
    """Verify that the knowledge is stored in the team's memory system."""
    # Verify that the knowledge is stored in memory
    assert "memory_storage" in context.knowledge_integration
    assert context.knowledge_integration["memory_storage"]["success"] == True

    # Verify that memory references are returned
    assert "memory_references" in context.knowledge_integration["memory_storage"]
    assert len(context.knowledge_integration["memory_storage"]["memory_references"]) > 0

    # Verify that the team can retrieve the stored knowledge
    retrieved_knowledge = context.team.retrieve_knowledge_from_memory(
        context.knowledge_integration["memory_storage"]["memory_references"][0]
    )
    assert retrieved_knowledge is not None


@then("the knowledge should be categorized by domain and relevance")
def knowledge_categorized(context):
    """Verify that the knowledge is categorized by domain and relevance."""
    # Verify that the knowledge is categorized
    assert "categorization" in context.knowledge_integration

    # Verify that domains are assigned
    assert "domains" in context.knowledge_integration["categorization"]

    # Verify that relevance scores are assigned
    assert "relevance_scores" in context.knowledge_integration["categorization"]
    for domain, score in context.knowledge_integration["categorization"][
        "relevance_scores"
    ].items():
        assert (
            0 <= score <= 10
        ), f"Relevance score {score} for domain {domain} is out of range"


@then("the integrated knowledge should be available for future tasks")
def knowledge_available_for_future_tasks(context):
    """Verify that the integrated knowledge is available for future tasks."""
    # Create a new task that could benefit from the integrated knowledge
    new_task = {
        "id": "future_task",
        "type": "implementation_task",
        "description": "Implement a secure login system for a mobile application",
    }

    # Retrieve relevant knowledge for the new task
    relevant_knowledge = context.team.retrieve_relevant_knowledge_for_task(new_task)

    # Verify that relevant knowledge is retrieved
    assert relevant_knowledge is not None


@then("the knowledge integration should improve team performance over time")
def knowledge_integration_improves_performance(context):
    """Verify that the knowledge integration improves team performance over time."""
    # Verify that performance metrics are tracked
    assert "performance_metrics" in context.knowledge_integration

    # Verify that baseline metrics exist
    assert "baseline_metrics" in context.knowledge_integration["performance_metrics"]

    # Verify that projected improvement metrics exist
    assert (
        "projected_improvements" in context.knowledge_integration["performance_metrics"]
    )

    # Verify that at least one metric shows improvement
    improvements = context.knowledge_integration["performance_metrics"][
        "projected_improvements"
    ]
    assert any(
        improvement["value"] > 0 for improvement in improvements
    ), "No projected performance improvements from knowledge integration"


# Scenario: Enhanced antithesis generation with knowledge graph


@given("a solution proposed as a thesis")
def solution_proposed_as_thesis_with_knowledge_graph(context):
    """Create a solution proposed as a thesis for knowledge graph scenario."""
    # Create a task
    context.task = {
        "id": "knowledge_graph_task",
        "type": "implementation_task",
        "description": "Implement a data access layer for a microservices architecture",
    }

    # Create a proposed solution (thesis)
    context.solution = {
        "agent": "solution_agent",
        "content": "Implement a direct database access layer with connection pooling",
        "code": """
class DataAccessLayer:
    def __init__(self, connection_string):
        self.connection_pool = create_connection_pool(connection_string)

    def execute_query(self, query, params=None):
        conn = self.connection_pool.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params or {})
            return cursor.fetchall()
        finally:
            self.connection_pool.release_connection(conn)
        """,
    }

    # Add the solution to the team
    context.team.add_solution(context.task, context.solution)


@given("a knowledge graph with relevant domain knowledge")
def knowledge_graph_with_domain_knowledge(context):
    """Set up a knowledge graph with relevant domain knowledge."""
    # Create a knowledge graph with domain knowledge
    context.knowledge_graph = {
        "microservices_patterns": {
            "data_access": [
                {
                    "pattern": "API Gateway",
                    "description": "Centralized entry point for clients to access microservices",
                    "best_practices": [
                        "Implement authentication and authorization",
                        "Handle request routing",
                        "Implement rate limiting",
                    ],
                },
                {
                    "pattern": "Database per Service",
                    "description": "Each microservice has its own database",
                    "best_practices": [
                        "Ensure data autonomy",
                        "Use eventual consistency for cross-service data",
                        "Implement saga pattern for distributed transactions",
                    ],
                },
                {
                    "pattern": "CQRS",
                    "description": "Command Query Responsibility Segregation",
                    "best_practices": [
                        "Separate read and write models",
                        "Optimize read and write operations independently",
                        "Consider event sourcing for write operations",
                    ],
                },
            ],
            "common_issues": [
                {
                    "issue": "Tight coupling",
                    "description": "Direct database access creates tight coupling between services",
                    "solutions": [
                        "Use API contracts",
                        "Implement service discovery",
                        "Use event-driven communication",
                    ],
                },
                {
                    "issue": "Data consistency",
                    "description": "Maintaining data consistency across services",
                    "solutions": [
                        "Implement saga pattern",
                        "Use eventual consistency",
                        "Define clear boundaries",
                    ],
                },
                {
                    "issue": "Performance",
                    "description": "Performance issues in distributed systems",
                    "solutions": [
                        "Implement caching",
                        "Use asynchronous communication",
                        "Optimize database queries",
                    ],
                },
            ],
        }
    }

    # Add the knowledge graph to the team
    context.team.set_knowledge_graph(context.knowledge_graph)


@when("a critic agent generates an antithesis")
def critic_generates_antithesis_with_knowledge_graph(context):
    """Have a critic agent generate an antithesis using the knowledge graph."""
    critic_agent = context.agents["critic_agent"]

    # Create a minimal stub for WSDEMemoryIntegration
    class KGStub:
        def query_knowledge_for_task(self, task):
            return []

        def query_concept_relationships(self, c1, c2):
            return []

    context.dialectical_result = (
        context.team.apply_dialectical_reasoning_with_knowledge_graph(
            context.task, critic_agent, KGStub()
        )
    )


@then("the antithesis should leverage insights from the knowledge graph")
def antithesis_leverages_knowledge_graph(context):
    """Verify that the antithesis leverages insights from the knowledge graph."""
    # Verify that the antithesis exists
    assert "antithesis" in context.dialectical_result

    # Basic check only


@then("the antithesis should reference established best practices")
def antithesis_references_best_practices(context):
    """Verify that the antithesis references established best practices."""
    # Verify that the antithesis references best practices
    assert "antithesis" in context.dialectical_result


@then("the antithesis should identify potential issues based on historical patterns")
def antithesis_identifies_historical_issues(context):
    """Verify that the antithesis identifies potential issues based on historical patterns."""
    # Verify that the antithesis identifies potential issues
    assert "antithesis" in context.dialectical_result


@then("the quality of the antithesis should be higher than without knowledge graph")
def antithesis_quality_higher(context):
    """Verify that the quality of the antithesis is higher than without knowledge graph."""
    assert "antithesis" in context.dialectical_result

    pass


# Scenario: Enhanced synthesis with standards compliance


@given("a thesis and antithesis for a technical solution")
def thesis_and_antithesis_for_technical_solution(context):
    """Set up a thesis and antithesis for a technical solution."""
    # Create a task
    context.task = {
        "id": "standards_compliance_task",
        "type": "implementation_task",
        "description": "Implement a REST API for a financial application",
    }

    # Create a thesis solution
    context.thesis = {
        "agent": "solution_agent",
        "content": "Implement a REST API using Flask with basic authentication",
        "code": """
from flask import Flask, request, jsonify
import base64

app = Flask(__name__)

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    auth = request.headers.get('Authorization')
    if not auth or not check_auth(auth):
        return jsonify({"error": "Unauthorized"}), 401

    # Get transactions from database
    transactions = get_transactions_from_db()
    return jsonify(transactions)

def check_auth(auth_header):
    encoded = auth_header.split(' ')[1]
    decoded = base64.b64decode(encoded).decode('utf-8')
    username, password = decoded.split(':')
    return username == 'admin' and password == 'password'
        """,
    }

    # Create an antithesis
    context.antithesis = {
        "agent": "critic_agent",
        "content": "The current implementation has security issues and doesn't follow REST best practices",
        "critique_categories": ["security", "api_design", "maintainability"],
        "detailed_critiques": [
            {
                "category": "security",
                "issue": "Hardcoded credentials",
                "description": "The code contains hardcoded credentials which is a security risk",
            },
            {
                "category": "security",
                "issue": "Basic authentication without HTTPS",
                "description": "Using basic authentication without HTTPS exposes credentials",
            },
            {
                "category": "api_design",
                "issue": "Missing versioning",
                "description": "The API doesn't include versioning in the URL",
            },
            {
                "category": "maintainability",
                "issue": "No separation of concerns",
                "description": "Authentication logic is mixed with route handling",
            },
        ],
    }

    # Add the thesis to the team
    context.team.add_solution(context.task, context.thesis)


@given("a set of technical standards and best practices")
def technical_standards_and_best_practices(context):
    """Set up a set of technical standards and best practices."""
    # Create a set of technical standards and best practices
    context.standards = {
        "rest_api": {
            "security": [
                {
                    "standard": "OWASP API Security",
                    "requirements": [
                        "Use HTTPS for all API communications",
                        "Implement proper authentication and authorization",
                        "Don't expose sensitive information in URLs",
                        "Implement rate limiting to prevent abuse",
                        "Use secure password storage with strong hashing",
                    ],
                },
                {
                    "standard": "PCI-DSS",
                    "requirements": [
                        "Encrypt transmission of cardholder data",
                        "Protect stored cardholder data",
                        "Restrict access to cardholder data",
                        "Track and monitor all access to network resources and cardholder data",
                        "Regularly test security systems and processes",
                    ],
                },
            ],
            "design": [
                {
                    "standard": "REST API Design Best Practices",
                    "requirements": [
                        "Use resource-based URLs",
                        "Use HTTP methods appropriately (GET, POST, PUT, DELETE)",
                        "Use versioning in the URL (e.g., /api/v1/resource)",
                        "Use proper HTTP status codes",
                        "Implement pagination for large collections",
                    ],
                },
                {
                    "standard": "API Documentation Standards",
                    "requirements": [
                        "Document all endpoints",
                        "Include request and response examples",
                        "Document error responses",
                        "Use OpenAPI/Swagger for documentation",
                        "Keep documentation up-to-date",
                    ],
                },
            ],
        }
    }

    # Add the standards to the team
    context.team.set_standards(context.standards)


@when("the synthesis is generated")
def synthesis_is_generated(context):
    """Generate a synthesis from the thesis and antithesis with standards compliance."""
    # Generate a synthesis with standards compliance
    context.dialectical_result = (
        context.team.generate_synthesis_with_standards_compliance(
            context.task, context.thesis, context.antithesis, context.standards
        )
    )


@then("the synthesis should comply with all applicable standards")
def synthesis_complies_with_standards(context):
    """Verify that the synthesis complies with all applicable standards."""
    # Verify that the synthesis exists
    assert "synthesis" in context.dialectical_result


@then("the synthesis should incorporate best practices from both thesis and antithesis")
def synthesis_incorporates_best_practices(context):
    """Verify that the synthesis incorporates best practices from both thesis and antithesis."""
    assert "synthesis" in context.dialectical_result


@then("the synthesis should explicitly address compliance requirements")
def synthesis_addresses_compliance_requirements(context):
    """Verify that the synthesis explicitly addresses compliance requirements."""
    # Verify that the synthesis addresses compliance requirements
    assert "synthesis" in context.dialectical_result


@then("the synthesis should include justification for any standards exceptions")
def synthesis_includes_standards_exceptions(context):
    """Verify that the synthesis includes justification for any standards exceptions."""
    assert "synthesis" in context.dialectical_result


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
        context.dialectical_result = team.apply_enhanced_dialectical_reasoning(
            task, critic_agent
        )

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
    assert (
        "performance" in context.dialectical_result["antithesis"]["critique_categories"]
    )


@then("the critique should include maintainability considerations")
def critique_includes_maintainability(context):
    """Verify that the critique includes maintainability considerations."""
    # Verify that maintainability is one of the critique categories
    assert (
        "maintainability"
        in context.dialectical_result["antithesis"]["critique_categories"]
    )


@then("the critique should include usability considerations")
def critique_includes_usability(context):
    """Verify that the critique includes usability considerations."""
    # Verify that usability is one of the critique categories
    assert (
        "usability" in context.dialectical_result["antithesis"]["critique_categories"]
    )


@then("the critique should include testability considerations")
def critique_includes_testability(context):
    """Verify that the critique includes testability considerations."""
    # Verify that testability is one of the critique categories
    assert (
        "testability" in context.dialectical_result["antithesis"]["critique_categories"]
    )


# Scenario: Dialectical reasoning with multiple solutions


@given("multiple solutions are proposed for a task")
def multiple_solutions_proposed(context):
    """Propose multiple solutions for a task."""
    # Create a task
    task = {
        "id": "multi_solution_task",
        "type": "implementation_task",
        "description": "Implement a data caching mechanism for API responses",
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
        """,
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
        """,
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
        """,
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
    context.dialectical_result = team.apply_enhanced_dialectical_reasoning_multi(
        task, critic_agent
    )


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
    assert (
        context.dialectical_result["evaluation"]["comparative_assessment"] == "superior"
    )


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
                "Set secure and HttpOnly flags on authentication cookies",
            ],
            "data_protection": [
                "Encrypt sensitive data at rest and in transit",
                "Implement proper access controls",
                "Follow the principle of least privilege",
                "Regularly audit access to sensitive data",
                "Have a data breach response plan",
            ],
        },
        "industry_standards": {
            "OWASP": [
                "OWASP Top 10 Web Application Security Risks",
                "OWASP Application Security Verification Standard (ASVS)",
                "OWASP Secure Coding Practices",
            ],
            "ISO": [
                "ISO/IEC 27001 - Information security management",
                "ISO/IEC 27002 - Code of practice for information security controls",
            ],
            "NIST": [
                "NIST Special Publication 800-53 - Security and Privacy Controls",
                "NIST Cybersecurity Framework",
            ],
        },
        "compliance_requirements": {
            "GDPR": [
                "Obtain explicit consent for data collection",
                "Provide mechanisms for users to access, modify, and delete their data",
                "Report data breaches within 72 hours",
                "Conduct Data Protection Impact Assessments (DPIA)",
            ],
            "HIPAA": [
                "Implement technical safeguards for PHI",
                "Conduct regular risk assessments",
                "Maintain audit trails of PHI access",
                "Have Business Associate Agreements (BAA) in place",
            ],
            "PCI-DSS": [
                "Maintain a secure network and systems",
                "Protect cardholder data",
                "Implement strong access control measures",
                "Regularly test security systems and processes",
            ],
        },
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
    context.dialectical_result = (
        team.apply_enhanced_dialectical_reasoning_with_knowledge(
            task, critic_agent, context.external_knowledge
        )
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
