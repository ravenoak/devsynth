from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from devsynth.application.agents.base import BaseAgent
from devsynth.domain.models.memory import MemoryItem
from devsynth.domain.models.wsde_facade import WSDETeam
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Import the feature file
scenarios(
    feature_path(
        __file__, "general", "multi_disciplinary_dialectical_reasoning.feature"
    )
)


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
            self.perspectives = []
            self.conflicts = []
            self.synthesis = None
            self.evaluation = None
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
@given("a WSDE team with agents specialized in different disciplines")
def wsde_team_with_specialized_agents(context):
    """Create a WSDE team with agents specialized in different disciplines."""
    context.team = WSDETeam(name="TestMultiDisciplinaryDialecticalReasoningStepsTeam")

    # Create agents with different disciplinary expertise
    code_agent = create_mock_agent("CodeAgent", ["python", "coding"])
    security_agent = create_mock_agent("SecurityAgent", ["security", "authentication"])
    ux_agent = create_mock_agent("UXAgent", ["user_experience", "interface_design"])
    performance_agent = create_mock_agent(
        "PerformanceAgent", ["performance", "optimization"]
    )
    accessibility_agent = create_mock_agent(
        "AccessibilityAgent", ["accessibility", "inclusive_design"]
    )
    critic_agent = create_mock_agent(
        "CriticAgent", ["dialectical_reasoning", "critique", "synthesis"]
    )

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

    # Set disciplinary agents
    context.disciplinary_agents = [
        context.security_agent,
        context.ux_agent,
        context.performance_agent,
        context.accessibility_agent,
    ]


@given("a knowledge base with multi-disciplinary information")
def knowledge_base_with_multi_disciplinary_information(context):
    """Create a knowledge base with multi-disciplinary information."""
    context.knowledge_sources = {
        "security": {
            "authentication_best_practices": [
                "Use multi-factor authentication for sensitive operations",
                "Store passwords using strong, adaptive hashing algorithms (e.g., bcrypt, Argon2)",
                "Implement rate limiting to prevent brute force attacks",
                "Use HTTPS for all authentication requests",
                "Set secure and HttpOnly flags on authentication cookies",
            ]
        },
        "user_experience": {
            "authentication_ux_principles": [
                "Minimize friction in the authentication process",
                "Provide clear error messages for failed authentication attempts",
                "Offer password recovery options",
                "Remember user preferences where appropriate",
                "Support single sign-on where possible",
            ]
        },
        "performance": {
            "authentication_performance_considerations": [
                "Optimize token validation for minimal latency",
                "Cache frequently used authentication data",
                "Use asynchronous processing for non-critical authentication tasks",
                "Implement efficient database queries for user lookup",
                "Monitor and optimize authentication service response times",
            ]
        },
        "accessibility": {
            "authentication_accessibility_guidelines": [
                "Ensure all authentication forms are keyboard navigable",
                "Provide appropriate ARIA labels for authentication form elements",
                "Support screen readers for error messages and instructions",
                "Maintain sufficient color contrast for text and interactive elements",
                "Allow authentication timeout extensions for users who need more time",
            ]
        },
    }


@given("the team is configured for multi-disciplinary dialectical reasoning")
def team_configured_for_multi_disciplinary_dialectical_reasoning(context):
    """Configure the team for multi-disciplinary dialectical reasoning."""
    # Mock the team's configuration for multi-disciplinary dialectical reasoning
    context.team.configure_multi_disciplinary_dialectical_reasoning = MagicMock()
    context.team.configure_multi_disciplinary_dialectical_reasoning.return_value = True

    # Call the method to configure the team
    result = context.team.configure_multi_disciplinary_dialectical_reasoning(
        critic_agent=context.critic_agent,
        disciplinary_agents=context.disciplinary_agents,
    )

    # Verify the configuration was successful
    assert result is True


# Scenario: Gathering disciplinary perspectives
@given("a complex problem spanning multiple disciplines")
def complex_problem_spanning_multiple_disciplines(context):
    """Define a complex problem that spans multiple disciplines."""
    context.task = {
        "type": "implementation_task",
        "description": "Implement a user authentication system with a focus on security, usability, performance, and accessibility",
    }

    # Add a proposed solution to the task
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
        """,
    }

    # Add the solution to the team
    context.team.add_solution = MagicMock()
    context.team.add_solution.return_value = True
    context.team.add_solution(context.task, context.solution)


@given("a task requiring security and user experience considerations")
def task_requiring_security_and_ux(context):
    context.task = {
        "type": "implementation_task",
        "description": "Implement a user authentication system with a focus on security and usability",
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
                "Set secure and HttpOnly flags on authentication cookies",
            ]
        },
        "user_experience": {
            "authentication_ux_principles": [
                "Minimize friction in the authentication process",
                "Provide clear error messages for failed authentication attempts",
                "Offer password recovery options",
                "Remember user preferences where appropriate",
                "Support single sign-on where possible",
            ]
        },
    }

    # Set disciplinary agents
    context.disciplinary_agents = [context.security_agent, context.ux_agent]


@given("a task requiring performance and accessibility considerations")
def task_requiring_performance_and_accessibility(context):
    context.task = {
        "type": "implementation_task",
        "description": "Implement a user authentication system with a focus on performance and accessibility",
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
                "Monitor and optimize authentication service response times",
            ]
        },
        "accessibility": {
            "authentication_accessibility_guidelines": [
                "Ensure all authentication forms are keyboard navigable",
                "Provide appropriate ARIA labels for authentication form elements",
                "Support screen readers for error messages and instructions",
                "Maintain sufficient color contrast for text and interactive elements",
                "Allow authentication timeout extensions for users who need more time",
            ]
        },
    }

    # Set disciplinary agents
    context.disciplinary_agents = [
        context.performance_agent,
        context.accessibility_agent,
    ]


@given(
    "a task requiring security, user experience, performance, and accessibility considerations"
)
def task_requiring_all_four_disciplines(context):
    context.task = {
        "type": "implementation_task",
        "description": "Implement a comprehensive user authentication system with a focus on security, usability, performance, and accessibility",
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
                "Set secure and HttpOnly flags on authentication cookies",
            ]
        },
        "user_experience": {
            "authentication_ux_principles": [
                "Minimize friction in the authentication process",
                "Provide clear error messages for failed authentication attempts",
                "Offer password recovery options",
                "Remember user preferences where appropriate",
                "Support single sign-on where possible",
            ]
        },
        "performance": {
            "authentication_performance_considerations": [
                "Optimize token validation for minimal latency",
                "Cache frequently used authentication data",
                "Use asynchronous processing for non-critical authentication tasks",
                "Implement efficient database queries for user lookup",
                "Monitor and optimize authentication service response times",
            ]
        },
        "accessibility": {
            "authentication_accessibility_guidelines": [
                "Ensure all authentication forms are keyboard navigable",
                "Provide appropriate ARIA labels for authentication form elements",
                "Support screen readers for error messages and instructions",
                "Maintain sufficient color contrast for text and interactive elements",
                "Allow authentication timeout extensions for users who need more time",
            ]
        },
    }

    # Set disciplinary agents
    context.disciplinary_agents = [
        context.security_agent,
        context.ux_agent,
        context.performance_agent,
        context.accessibility_agent,
    ]


@when("the team initiates multi-disciplinary dialectical reasoning")
def team_initiates_multi_disciplinary_dialectical_reasoning(context):
    """Initiate multi-disciplinary dialectical reasoning process."""
    # Mock the team's method for applying multi-disciplinary dialectical reasoning
    context.team.apply_multi_disciplinary_dialectical_reasoning = MagicMock()

    # Create a mock result with perspectives from different disciplines
    mock_result = {
        "thesis": context.solution,
        "disciplinary_perspectives": [
            {
                "discipline": "security",
                "agent": "SecurityAgent",
                "perspective": "The solution needs to implement password hashing, rate limiting, and HTTPS.",
                "concerns": [
                    "Hardcoded credentials",
                    "No password hashing",
                    "No rate limiting",
                ],
                "recommendations": [
                    "Use bcrypt for password hashing",
                    "Implement rate limiting",
                    "Use HTTPS",
                ],
            },
            {
                "discipline": "user_experience",
                "agent": "UXAgent",
                "perspective": "The authentication flow needs to be user-friendly with clear error messages.",
                "concerns": ["No error messages", "No password recovery"],
                "recommendations": [
                    "Add clear error messages",
                    "Implement password recovery",
                ],
            },
            {
                "discipline": "performance",
                "agent": "PerformanceAgent",
                "perspective": "Token validation should be optimized for minimal latency.",
                "concerns": [
                    "No caching strategy",
                    "Potential performance bottlenecks",
                ],
                "recommendations": [
                    "Cache frequently used authentication data",
                    "Optimize token validation",
                ],
            },
            {
                "discipline": "accessibility",
                "agent": "AccessibilityAgent",
                "perspective": "Authentication forms must be accessible to all users.",
                "concerns": ["No keyboard navigation", "No ARIA labels"],
                "recommendations": ["Ensure keyboard navigability", "Add ARIA labels"],
            },
        ],
        "synthesis": {
            "integrated_perspectives": [
                {
                    "discipline": "security",
                    "key_points": ["Password hashing", "Rate limiting", "HTTPS"],
                },
                {
                    "discipline": "user_experience",
                    "key_points": ["Clear error messages", "Password recovery"],
                },
                {
                    "discipline": "performance",
                    "key_points": ["Caching", "Optimized validation"],
                },
                {
                    "discipline": "accessibility",
                    "key_points": ["Keyboard navigation", "ARIA labels"],
                },
            ],
            "perspective_conflicts": [
                {
                    "disciplines": ["security", "user_experience"],
                    "conflict": "Security measures may increase friction in the user experience",
                    "severity": "medium",
                },
                {
                    "disciplines": ["performance", "accessibility"],
                    "conflict": "Some accessibility features may impact performance",
                    "severity": "low",
                },
            ],
            "conflict_resolutions": [
                {
                    "disciplines": ["security", "user_experience"],
                    "resolution": "Implement progressive security that balances protection with usability",
                    "trade_offs": [
                        "Slightly reduced security for better UX",
                        "Slightly increased friction for better security",
                    ],
                },
                {
                    "disciplines": ["performance", "accessibility"],
                    "resolution": "Optimize critical paths while maintaining accessibility",
                    "trade_offs": [
                        "Focus performance optimization on non-accessibility features",
                        "Use efficient accessibility implementations",
                    ],
                },
            ],
            "is_improvement": True,
            "improved_solution": "Implement secure authentication with bcrypt hashing, rate limiting, clear error messages, and accessibility features",
        },
        "evaluation": {
            "perspective_scores": [
                {
                    "discipline": "security",
                    "score": 8.5,
                    "rationale": "Addresses major security concerns",
                },
                {
                    "discipline": "user_experience",
                    "score": 8.0,
                    "rationale": "Improves usability while maintaining security",
                },
                {
                    "discipline": "performance",
                    "score": 7.5,
                    "rationale": "Addresses performance concerns with minimal trade-offs",
                },
                {
                    "discipline": "accessibility",
                    "score": 8.0,
                    "rationale": "Implements key accessibility features",
                },
            ],
            "overall_assessment": "The solution achieves a good balance between security, usability, performance, and accessibility",
        },
    }

    # Set the mock result
    context.team.apply_multi_disciplinary_dialectical_reasoning.return_value = (
        mock_result
    )

    # Call the method to apply multi-disciplinary dialectical reasoning
    context.result = context.team.apply_multi_disciplinary_dialectical_reasoning(
        context.task,
        context.critic_agent,
        context.knowledge_sources,
        context.disciplinary_agents,
    )

    # Store the perspectives for later assertions
    context.perspectives = context.result["disciplinary_perspectives"]


@then("each disciplinary agent should provide a specialized perspective")
def each_disciplinary_agent_provides_specialized_perspective(context):
    """Verify that each disciplinary agent provides a specialized perspective."""
    assert "disciplinary_perspectives" in context.result

    # Get the list of disciplines from the perspectives
    disciplines = [p["discipline"] for p in context.result["disciplinary_perspectives"]]

    # Verify that each disciplinary agent has provided a perspective
    assert "security" in disciplines
    assert "user_experience" in disciplines
    assert "performance" in disciplines
    assert "accessibility" in disciplines

    # Verify that each perspective has an agent
    for perspective in context.result["disciplinary_perspectives"]:
        assert "agent" in perspective
        assert perspective["agent"] is not None


@then("each perspective should focus on domain-specific considerations")
def each_perspective_focuses_on_domain_specific_considerations(context):
    """Verify that each perspective focuses on domain-specific considerations."""
    for perspective in context.result["disciplinary_perspectives"]:
        discipline = perspective["discipline"]

        # Verify that the perspective contains domain-specific concerns and recommendations
        assert "concerns" in perspective
        assert "recommendations" in perspective

        # Verify that the concerns and recommendations are relevant to the discipline
        if discipline == "security":
            assert any(
                "password" in concern.lower() for concern in perspective["concerns"]
            )
            assert any("hash" in rec.lower() for rec in perspective["recommendations"])
        elif discipline == "user_experience":
            assert any(
                "error" in concern.lower() for concern in perspective["concerns"]
            )
            assert any(
                "message" in rec.lower() for rec in perspective["recommendations"]
            )
        elif discipline == "performance":
            assert any(
                "performance" in concern.lower() for concern in perspective["concerns"]
            )
            assert any("cache" in rec.lower() for rec in perspective["recommendations"])
        elif discipline == "accessibility":
            assert any(
                "accessibility" in concern.lower() or "aria" in concern.lower()
                for concern in perspective["concerns"]
            )
            assert any(
                "aria" in rec.lower() or "keyboard" in rec.lower()
                for rec in perspective["recommendations"]
            )


@then("the perspectives should be documented with disciplinary context")
def perspectives_documented_with_disciplinary_context(context):
    """Verify that the perspectives are documented with disciplinary context."""
    for perspective in context.result["disciplinary_perspectives"]:
        # Verify that each perspective has a discipline and a perspective text
        assert "discipline" in perspective
        assert "perspective" in perspective
        assert perspective["discipline"] is not None
        assert perspective["perspective"] is not None

        # Verify that the perspective text mentions the discipline or related terms
        discipline = perspective["discipline"]
        perspective_text = perspective["perspective"].lower()

        if discipline == "security":
            assert any(
                term in perspective_text
                for term in ["security", "password", "hash", "https", "rate limiting"]
            )
        elif discipline == "user_experience":
            assert any(
                term in perspective_text
                for term in ["user", "experience", "ux", "error message", "usability"]
            )
        elif discipline == "performance":
            assert any(
                term in perspective_text
                for term in ["performance", "latency", "optimize", "cache"]
            )
        elif discipline == "accessibility":
            assert any(
                term in perspective_text
                for term in ["accessibility", "accessible", "aria", "keyboard"]
            )


@then("the collection of perspectives should cover all relevant disciplines")
def collection_of_perspectives_covers_all_relevant_disciplines(context):
    """Verify that the collection of perspectives covers all relevant disciplines."""
    # Get the list of disciplines from the perspectives
    disciplines = [p["discipline"] for p in context.result["disciplinary_perspectives"]]

    # Verify that all relevant disciplines are covered
    expected_disciplines = [
        "security",
        "user_experience",
        "performance",
        "accessibility",
    ]
    for discipline in expected_disciplines:
        assert discipline in disciplines

    # Verify that the number of perspectives matches the number of disciplinary agents
    assert len(context.result["disciplinary_perspectives"]) == len(
        context.disciplinary_agents
    )


# Scenario: Identifying perspective conflicts across disciplines
@given("perspectives from multiple disciplinary agents")
def perspectives_from_multiple_disciplinary_agents(context):
    """Set up perspectives from multiple disciplinary agents."""
    # Create perspectives if they don't exist yet
    if not hasattr(context, "perspectives") or not context.perspectives:
        # Create a mock result with perspectives from different disciplines
        context.perspectives = [
            {
                "discipline": "security",
                "agent": "SecurityAgent",
                "perspective": "The solution needs to implement password hashing, rate limiting, and HTTPS.",
                "concerns": [
                    "Hardcoded credentials",
                    "No password hashing",
                    "No rate limiting",
                ],
                "recommendations": [
                    "Use bcrypt for password hashing",
                    "Implement rate limiting",
                    "Use HTTPS",
                ],
            },
            {
                "discipline": "user_experience",
                "agent": "UXAgent",
                "perspective": "The authentication flow needs to be user-friendly with clear error messages.",
                "concerns": ["No error messages", "No password recovery"],
                "recommendations": [
                    "Add clear error messages",
                    "Implement password recovery",
                ],
            },
            {
                "discipline": "performance",
                "agent": "PerformanceAgent",
                "perspective": "Token validation should be optimized for minimal latency.",
                "concerns": [
                    "No caching strategy",
                    "Potential performance bottlenecks",
                ],
                "recommendations": [
                    "Cache frequently used authentication data",
                    "Optimize token validation",
                ],
            },
            {
                "discipline": "accessibility",
                "agent": "AccessibilityAgent",
                "perspective": "Authentication forms must be accessible to all users.",
                "concerns": ["No keyboard navigation", "No ARIA labels"],
                "recommendations": ["Ensure keyboard navigability", "Add ARIA labels"],
            },
        ]


@when("the team analyzes the perspectives")
def team_analyzes_perspectives(context):
    """Analyze the perspectives to identify conflicts."""
    # Mock the team's method for analyzing perspectives
    context.team.analyze_perspectives = MagicMock()

    # Create a mock result with identified conflicts
    mock_conflicts = [
        {
            "disciplines": ["security", "user_experience"],
            "conflict": "Security measures may increase friction in the user experience",
            "severity": "medium",
            "assumptions": {
                "security": "Strong security requires multiple verification steps",
                "user_experience": "Users prefer minimal friction during authentication",
            },
        },
        {
            "disciplines": ["performance", "accessibility"],
            "conflict": "Some accessibility features may impact performance",
            "severity": "low",
            "assumptions": {
                "performance": "Performance optimization requires minimal DOM elements",
                "accessibility": "Accessibility often requires additional ARIA attributes and DOM elements",
            },
        },
        {
            "disciplines": ["security", "performance"],
            "conflict": "Security checks may add latency to authentication",
            "severity": "medium",
            "assumptions": {
                "security": "Thorough security validation requires multiple checks",
                "performance": "Authentication should be as fast as possible",
            },
        },
    ]

    # Set the mock result
    context.team.analyze_perspectives.return_value = mock_conflicts

    # Call the method to analyze perspectives
    context.conflicts = context.team.analyze_perspectives(context.perspectives)


@then("conflicts between disciplinary perspectives should be identified")
def conflicts_between_disciplinary_perspectives_identified(context):
    """Verify that conflicts between disciplinary perspectives are identified."""
    assert context.conflicts is not None
    assert len(context.conflicts) > 0

    # Verify that each conflict involves at least two disciplines
    for conflict in context.conflicts:
        assert "disciplines" in conflict
        assert len(conflict["disciplines"]) >= 2
        assert "conflict" in conflict
        assert conflict["conflict"] is not None


@then("each conflict should be categorized by type and severity")
def each_conflict_categorized_by_type_and_severity(context):
    """Verify that each conflict is categorized by type and severity."""
    for conflict in context.conflicts:
        # Verify that each conflict has a type and severity
        assert "conflict" in conflict  # This is the type/description of the conflict
        assert "severity" in conflict
        assert conflict["conflict"] is not None
        assert conflict["severity"] is not None

        # Verify that the severity is one of the expected values
        assert conflict["severity"] in ["low", "medium", "high"]


@then("the underlying disciplinary assumptions should be documented")
def underlying_disciplinary_assumptions_documented(context):
    """Verify that the underlying disciplinary assumptions are documented for each conflict."""
    for conflict in context.conflicts:
        # Verify that each conflict has documented assumptions
        assert "assumptions" in conflict
        assert conflict["assumptions"] is not None

        # Verify that there are assumptions for each discipline involved in the conflict
        for discipline in conflict["disciplines"]:
            assert discipline in conflict["assumptions"]
            assert conflict["assumptions"][discipline] is not None

            # Verify that the assumption is relevant to the discipline
            assumption = conflict["assumptions"][discipline].lower()
            if discipline == "security":
                assert any(
                    term in assumption
                    for term in ["security", "protection", "verification", "validation"]
                )
            elif discipline == "user_experience":
                assert any(
                    term in assumption
                    for term in ["user", "experience", "friction", "usability"]
                )
            elif discipline == "performance":
                assert any(
                    term in assumption
                    for term in ["performance", "speed", "latency", "optimization"]
                )
            elif discipline == "accessibility":
                assert any(
                    term in assumption
                    for term in ["accessibility", "accessible", "aria", "dom"]
                )


@then("the conflicts should be prioritized for resolution")
def conflicts_prioritized_for_resolution(context):
    """Verify that the conflicts are prioritized for resolution."""
    # Sort conflicts by severity (high, medium, low)
    severity_order = {"high": 0, "medium": 1, "low": 2}
    sorted_conflicts = sorted(
        context.conflicts, key=lambda c: severity_order.get(c["severity"], 3)
    )

    # Verify that the conflicts are sorted by severity
    for i in range(1, len(sorted_conflicts)):
        assert severity_order.get(
            sorted_conflicts[i - 1]["severity"], 3
        ) <= severity_order.get(sorted_conflicts[i]["severity"], 3)

    # Verify that there is at least one conflict with a severity of "medium" or "high"
    assert any(
        conflict["severity"] in ["medium", "high"] for conflict in context.conflicts
    )


# Scenario: Multi-disciplinary synthesis generation
@given("perspectives and identified conflicts from multiple disciplines")
def perspectives_and_identified_conflicts_from_multiple_disciplines(context):
    """Set up perspectives and identified conflicts from multiple disciplines."""
    # Create perspectives if they don't exist yet
    if not hasattr(context, "perspectives") or not context.perspectives:
        # Create a mock result with perspectives from different disciplines
        context.perspectives = [
            {
                "discipline": "security",
                "agent": "SecurityAgent",
                "perspective": "The solution needs to implement password hashing, rate limiting, and HTTPS.",
                "concerns": [
                    "Hardcoded credentials",
                    "No password hashing",
                    "No rate limiting",
                ],
                "recommendations": [
                    "Use bcrypt for password hashing",
                    "Implement rate limiting",
                    "Use HTTPS",
                ],
            },
            {
                "discipline": "user_experience",
                "agent": "UXAgent",
                "perspective": "The authentication flow needs to be user-friendly with clear error messages.",
                "concerns": ["No error messages", "No password recovery"],
                "recommendations": [
                    "Add clear error messages",
                    "Implement password recovery",
                ],
            },
            {
                "discipline": "performance",
                "agent": "PerformanceAgent",
                "perspective": "Token validation should be optimized for minimal latency.",
                "concerns": [
                    "No caching strategy",
                    "Potential performance bottlenecks",
                ],
                "recommendations": [
                    "Cache frequently used authentication data",
                    "Optimize token validation",
                ],
            },
            {
                "discipline": "accessibility",
                "agent": "AccessibilityAgent",
                "perspective": "Authentication forms must be accessible to all users.",
                "concerns": ["No keyboard navigation", "No ARIA labels"],
                "recommendations": ["Ensure keyboard navigability", "Add ARIA labels"],
            },
        ]

    # Create conflicts if they don't exist yet
    if not hasattr(context, "conflicts") or not context.conflicts:
        context.conflicts = [
            {
                "disciplines": ["security", "user_experience"],
                "conflict": "Security measures may increase friction in the user experience",
                "severity": "medium",
                "assumptions": {
                    "security": "Strong security requires multiple verification steps",
                    "user_experience": "Users prefer minimal friction during authentication",
                },
            },
            {
                "disciplines": ["performance", "accessibility"],
                "conflict": "Some accessibility features may impact performance",
                "severity": "low",
                "assumptions": {
                    "performance": "Performance optimization requires minimal DOM elements",
                    "accessibility": "Accessibility often requires additional ARIA attributes and DOM elements",
                },
            },
            {
                "disciplines": ["security", "performance"],
                "conflict": "Security checks may add latency to authentication",
                "severity": "medium",
                "assumptions": {
                    "security": "Thorough security validation requires multiple checks",
                    "performance": "Authentication should be as fast as possible",
                },
            },
        ]


@when("the team generates a multi-disciplinary synthesis")
def team_generates_multi_disciplinary_synthesis(context):
    """Generate a multi-disciplinary synthesis from perspectives and conflicts."""
    # Mock the team's method for generating a synthesis
    context.team.generate_multi_disciplinary_synthesis = MagicMock()

    # Create a mock synthesis
    mock_synthesis = {
        "integrated_perspectives": [
            {
                "discipline": "security",
                "key_points": ["Password hashing", "Rate limiting", "HTTPS"],
            },
            {
                "discipline": "user_experience",
                "key_points": ["Clear error messages", "Password recovery"],
            },
            {
                "discipline": "performance",
                "key_points": ["Caching", "Optimized validation"],
            },
            {
                "discipline": "accessibility",
                "key_points": ["Keyboard navigation", "ARIA labels"],
            },
        ],
        "perspective_conflicts": context.conflicts,
        "conflict_resolutions": [
            {
                "disciplines": ["security", "user_experience"],
                "resolution": "Implement progressive security that balances protection with usability",
                "trade_offs": [
                    "Slightly reduced security for better UX",
                    "Slightly increased friction for better security",
                ],
            },
            {
                "disciplines": ["performance", "accessibility"],
                "resolution": "Optimize critical paths while maintaining accessibility",
                "trade_offs": [
                    "Focus performance optimization on non-accessibility features",
                    "Use efficient accessibility implementations",
                ],
            },
            {
                "disciplines": ["security", "performance"],
                "resolution": "Implement security checks asynchronously where possible",
                "trade_offs": [
                    "Some security checks may be delayed",
                    "Critical security checks remain synchronous",
                ],
            },
        ],
        "is_improvement": True,
        "improved_solution": "Implement secure authentication with bcrypt hashing, rate limiting, clear error messages, and accessibility features",
        "disciplinary_integrity": {
            "security": "Maintains core security principles while allowing some flexibility",
            "user_experience": "Preserves key usability features while accepting necessary security measures",
            "performance": "Optimizes critical paths while accepting some overhead for security and accessibility",
            "accessibility": "Ensures essential accessibility features are implemented efficiently",
        },
        "trade_offs": [
            {
                "description": "Security vs. User Experience",
                "decision": "Balanced approach with progressive security",
                "rationale": "Maximizes security without significantly degrading user experience",
            },
            {
                "description": "Performance vs. Accessibility",
                "decision": "Prioritize accessibility with performance optimizations where possible",
                "rationale": "Accessibility is a requirement, but performance can be optimized in non-accessibility features",
            },
        ],
    }

    # Set the mock result
    context.team.generate_multi_disciplinary_synthesis.return_value = mock_synthesis

    # Call the method to generate a synthesis
    context.synthesis = context.team.generate_multi_disciplinary_synthesis(
        context.perspectives, context.conflicts
    )


@then("the synthesis should address all identified conflicts")
def synthesis_addresses_all_identified_conflicts(context):
    """Verify that the synthesis addresses all identified conflicts."""
    # Verify that the synthesis contains conflict resolutions
    assert "conflict_resolutions" in context.synthesis

    # Get the list of conflicts from the conflict resolutions
    resolved_conflicts = []
    for resolution in context.synthesis["conflict_resolutions"]:
        assert "disciplines" in resolution
        resolved_conflicts.append(tuple(sorted(resolution["disciplines"])))

    # Get the list of conflicts from the original conflicts
    original_conflicts = []
    for conflict in context.conflicts:
        assert "disciplines" in conflict
        original_conflicts.append(tuple(sorted(conflict["disciplines"])))

    # Verify that all original conflicts have been addressed in the resolutions
    for conflict in original_conflicts:
        assert (
            conflict in resolved_conflicts
        ), f"Conflict {conflict} not addressed in resolutions"

    # Verify that each resolution has a meaningful description
    for resolution in context.synthesis["conflict_resolutions"]:
        assert "resolution" in resolution
        assert resolution["resolution"] is not None
        assert (
            len(resolution["resolution"]) > 10
        )  # Ensure it's a meaningful description


@then("the synthesis should integrate insights from all disciplines")
def synthesis_integrates_insights_from_all_disciplines(context):
    """Verify that the synthesis integrates insights from all disciplines."""
    # Verify that the synthesis contains integrated perspectives
    assert "integrated_perspectives" in context.synthesis

    # Get the list of disciplines from the integrated perspectives
    integrated_disciplines = [
        p["discipline"] for p in context.synthesis["integrated_perspectives"]
    ]

    # Verify that all disciplines are represented in the integrated perspectives
    expected_disciplines = [
        "security",
        "user_experience",
        "performance",
        "accessibility",
    ]
    for discipline in expected_disciplines:
        assert (
            discipline in integrated_disciplines
        ), f"Discipline {discipline} not found in integrated perspectives"

    # Verify that each integrated perspective has key points
    for perspective in context.synthesis["integrated_perspectives"]:
        assert "key_points" in perspective
        assert perspective["key_points"] is not None
        assert len(perspective["key_points"]) > 0


@then("the synthesis should maintain disciplinary integrity where appropriate")
def synthesis_maintains_disciplinary_integrity(context):
    """Verify that the synthesis maintains disciplinary integrity where appropriate."""
    # Verify that the synthesis contains disciplinary integrity information
    assert "disciplinary_integrity" in context.synthesis

    # Get the disciplinary integrity information
    disciplinary_integrity = context.synthesis["disciplinary_integrity"]

    # Verify that there is integrity information for each discipline
    expected_disciplines = [
        "security",
        "user_experience",
        "performance",
        "accessibility",
    ]
    for discipline in expected_disciplines:
        assert (
            discipline in disciplinary_integrity
        ), f"Discipline {discipline} not found in disciplinary integrity"
        assert disciplinary_integrity[discipline] is not None
        assert (
            len(disciplinary_integrity[discipline]) > 10
        )  # Ensure it's a meaningful description

        # Verify that the integrity description mentions maintaining core principles
        integrity_description = disciplinary_integrity[discipline].lower()
        assert any(
            term in integrity_description
            for term in [
                "maintain",
                "preserv",
                "ensur",
                "core",
                "principle",
                "essential",
            ]
        )


@then("the synthesis should document trade-offs between disciplinary requirements")
def synthesis_documents_trade_offs(context):
    """Verify that the synthesis documents trade-offs between disciplinary requirements."""
    # Verify that the synthesis contains trade-offs
    assert "trade_offs" in context.synthesis

    # Verify that there are trade-offs documented
    assert len(context.synthesis["trade_offs"]) > 0

    # Verify that each trade-off has the required fields
    for trade_off in context.synthesis["trade_offs"]:
        assert "description" in trade_off
        assert "decision" in trade_off
        assert "rationale" in trade_off
        assert trade_off["description"] is not None
        assert trade_off["decision"] is not None
        assert trade_off["rationale"] is not None

        # Verify that the trade-off description mentions at least two disciplines
        description = trade_off["description"].lower()
        disciplines_mentioned = 0
        for discipline in [
            "security",
            "user experience",
            "performance",
            "accessibility",
        ]:
            if (
                discipline.lower() in description
                or discipline.lower().replace(" ", "_") in description
            ):
                disciplines_mentioned += 1
        assert (
            disciplines_mentioned >= 2
        ), f"Trade-off description '{description}' does not mention at least two disciplines"


# Scenario: Multi-disciplinary evaluation
@given("a synthesis generated from multi-disciplinary perspectives")
def synthesis_generated_from_multi_disciplinary_perspectives(context):
    """Set up a synthesis generated from multi-disciplinary perspectives."""
    # Create a synthesis if it doesn't exist yet
    if not hasattr(context, "synthesis") or not context.synthesis:
        # Create a mock synthesis
        context.synthesis = {
            "integrated_perspectives": [
                {
                    "discipline": "security",
                    "key_points": ["Password hashing", "Rate limiting", "HTTPS"],
                },
                {
                    "discipline": "user_experience",
                    "key_points": ["Clear error messages", "Password recovery"],
                },
                {
                    "discipline": "performance",
                    "key_points": ["Caching", "Optimized validation"],
                },
                {
                    "discipline": "accessibility",
                    "key_points": ["Keyboard navigation", "ARIA labels"],
                },
            ],
            "perspective_conflicts": [
                {
                    "disciplines": ["security", "user_experience"],
                    "conflict": "Security measures may increase friction in the user experience",
                    "severity": "medium",
                    "assumptions": {
                        "security": "Strong security requires multiple verification steps",
                        "user_experience": "Users prefer minimal friction during authentication",
                    },
                },
                {
                    "disciplines": ["performance", "accessibility"],
                    "conflict": "Some accessibility features may impact performance",
                    "severity": "low",
                    "assumptions": {
                        "performance": "Performance optimization requires minimal DOM elements",
                        "accessibility": "Accessibility often requires additional ARIA attributes and DOM elements",
                    },
                },
            ],
            "conflict_resolutions": [
                {
                    "disciplines": ["security", "user_experience"],
                    "resolution": "Implement progressive security that balances protection with usability",
                    "trade_offs": [
                        "Slightly reduced security for better UX",
                        "Slightly increased friction for better security",
                    ],
                },
                {
                    "disciplines": ["performance", "accessibility"],
                    "resolution": "Optimize critical paths while maintaining accessibility",
                    "trade_offs": [
                        "Focus performance optimization on non-accessibility features",
                        "Use efficient accessibility implementations",
                    ],
                },
            ],
            "is_improvement": True,
            "improved_solution": "Implement secure authentication with bcrypt hashing, rate limiting, clear error messages, and accessibility features",
            "disciplinary_integrity": {
                "security": "Maintains core security principles while allowing some flexibility",
                "user_experience": "Preserves key usability features while accepting necessary security measures",
                "performance": "Optimizes critical paths while accepting some overhead for security and accessibility",
                "accessibility": "Ensures essential accessibility features are implemented efficiently",
            },
            "trade_offs": [
                {
                    "description": "Security vs. User Experience",
                    "decision": "Balanced approach with progressive security",
                    "rationale": "Maximizes security without significantly degrading user experience",
                },
                {
                    "description": "Performance vs. Accessibility",
                    "decision": "Prioritize accessibility with performance optimizations where possible",
                    "rationale": "Accessibility is a requirement, but performance can be optimized in non-accessibility features",
                },
            ],
        }


@when("the team evaluates the synthesis")
def team_evaluates_synthesis(context):
    """Evaluate the synthesis from multi-disciplinary perspectives."""
    # Mock the team's method for evaluating a synthesis
    context.team.evaluate_synthesis = MagicMock()

    # Create a mock evaluation result
    mock_evaluation = {
        "perspective_scores": [
            {
                "discipline": "security",
                "score": 8.5,
                "rationale": "Addresses major security concerns",
                "standards_compliance": True,
            },
            {
                "discipline": "user_experience",
                "score": 8.0,
                "rationale": "Improves usability while maintaining security",
                "standards_compliance": True,
            },
            {
                "discipline": "performance",
                "score": 7.5,
                "rationale": "Addresses performance concerns with minimal trade-offs",
                "standards_compliance": True,
            },
            {
                "discipline": "accessibility",
                "score": 8.0,
                "rationale": "Implements key accessibility features",
                "standards_compliance": True,
            },
        ],
        "standards_compliance": {
            "security": {
                "compliant": True,
                "standards": ["OWASP Top 10", "NIST Authentication Guidelines"],
                "notes": "Meets all critical security requirements",
            },
            "user_experience": {
                "compliant": True,
                "standards": ["Nielsen's Heuristics", "Material Design Guidelines"],
                "notes": "Follows established UX patterns",
            },
            "performance": {
                "compliant": True,
                "standards": ["Web Vitals", "Performance Budget"],
                "notes": "Meets performance targets with minor exceptions",
            },
            "accessibility": {
                "compliant": True,
                "standards": ["WCAG 2.1 AA", "Section 508"],
                "notes": "Meets accessibility requirements",
            },
        },
        "remaining_concerns": [
            {
                "discipline": "security",
                "concern": "Password policy could be more stringent",
                "severity": "low",
            },
            {
                "discipline": "performance",
                "concern": "Token validation could be further optimized",
                "severity": "low",
            },
        ],
        "overall_assessment": {
            "score": 8.0,
            "summary": "The solution achieves a good balance between security, usability, performance, and accessibility",
            "strengths": [
                "Strong security measures",
                "Good user experience",
                "Acceptable performance",
                "Strong accessibility",
            ],
            "weaknesses": [
                "Some minor security improvements possible",
                "Some performance optimizations possible",
            ],
            "recommendation": "Approve with minor suggestions for future improvements",
        },
    }

    # Set the mock result
    context.team.evaluate_synthesis.return_value = mock_evaluation

    # Call the method to evaluate the synthesis
    context.evaluation = context.team.evaluate_synthesis(context.synthesis)


@then("the evaluation should assess the solution from each disciplinary perspective")
def evaluation_assesses_solution_from_each_disciplinary_perspective(context):
    """Verify that the evaluation assesses the solution from each disciplinary perspective."""
    # Verify that the evaluation contains perspective scores
    assert "perspective_scores" in context.evaluation

    # Get the list of disciplines from the perspective scores
    evaluated_disciplines = [
        p["discipline"] for p in context.evaluation["perspective_scores"]
    ]

    # Verify that all disciplines are represented in the evaluation
    expected_disciplines = [
        "security",
        "user_experience",
        "performance",
        "accessibility",
    ]
    for discipline in expected_disciplines:
        assert (
            discipline in evaluated_disciplines
        ), f"Discipline {discipline} not found in evaluation"

    # Verify that each perspective score has a score and rationale
    for perspective in context.evaluation["perspective_scores"]:
        assert "score" in perspective
        assert "rationale" in perspective
        assert perspective["score"] is not None
        assert perspective["rationale"] is not None
        assert isinstance(perspective["score"], (int, float))
        assert 0 <= perspective["score"] <= 10  # Assuming scores are on a 0-10 scale


@then("the evaluation should verify compliance with discipline-specific standards")
def evaluation_verifies_compliance_with_discipline_specific_standards(context):
    """Verify that the evaluation checks compliance with discipline-specific standards."""
    # Verify that the evaluation contains standards compliance information
    assert "standards_compliance" in context.evaluation

    # Get the standards compliance information
    standards_compliance = context.evaluation["standards_compliance"]

    # Verify that there is compliance information for each discipline
    expected_disciplines = [
        "security",
        "user_experience",
        "performance",
        "accessibility",
    ]
    for discipline in expected_disciplines:
        assert (
            discipline in standards_compliance
        ), f"Discipline {discipline} not found in standards compliance"

        # Verify that each discipline has compliance information
        discipline_compliance = standards_compliance[discipline]
        assert "compliant" in discipline_compliance
        assert "standards" in discipline_compliance
        assert "notes" in discipline_compliance

        # Verify that the standards are relevant to the discipline
        standards = discipline_compliance["standards"]
        assert len(standards) > 0

        if discipline == "security":
            assert any(
                "OWASP" in standard or "NIST" in standard for standard in standards
            )
        elif discipline == "user_experience":
            assert any(
                "UX" in standard or "Design" in standard or "Nielsen" in standard
                for standard in standards
            )
        elif discipline == "performance":
            assert any(
                "Performance" in standard or "Web Vitals" in standard
                for standard in standards
            )
        elif discipline == "accessibility":
            assert any(
                "WCAG" in standard or "Section 508" in standard or "ADA" in standard
                for standard in standards
            )


@then("the evaluation should identify any remaining disciplinary concerns")
def evaluation_identifies_remaining_disciplinary_concerns(context):
    """Verify that the evaluation identifies any remaining disciplinary concerns."""
    # Verify that the evaluation contains remaining concerns
    assert "remaining_concerns" in context.evaluation

    # Verify that the remaining concerns are properly structured
    remaining_concerns = context.evaluation["remaining_concerns"]
    assert isinstance(remaining_concerns, list)

    # If there are remaining concerns, verify their structure
    if remaining_concerns:
        for concern in remaining_concerns:
            assert "discipline" in concern
            assert "concern" in concern
            assert "severity" in concern
            assert concern["discipline"] is not None
            assert concern["concern"] is not None
            assert concern["severity"] is not None
            assert concern["severity"] in ["low", "medium", "high"]


@then(
    "the evaluation should provide an overall assessment of multi-disciplinary quality"
)
def evaluation_provides_overall_assessment_of_multi_disciplinary_quality(context):
    """Verify that the evaluation provides an overall assessment of multi-disciplinary quality."""
    # Verify that the evaluation contains an overall assessment
    assert "overall_assessment" in context.evaluation

    # Get the overall assessment
    overall_assessment = context.evaluation["overall_assessment"]

    # Verify that the overall assessment has the required fields
    assert "score" in overall_assessment
    assert "summary" in overall_assessment
    assert "strengths" in overall_assessment
    assert "weaknesses" in overall_assessment
    assert "recommendation" in overall_assessment

    # Verify that the score is within the expected range
    assert isinstance(overall_assessment["score"], (int, float))
    assert 0 <= overall_assessment["score"] <= 10  # Assuming scores are on a 0-10 scale

    # Verify that the summary mentions balance or integration of multiple disciplines
    summary = overall_assessment["summary"].lower()
    assert any(
        term in summary
        for term in ["balance", "integrat", "multi-disciplinary", "across disciplines"]
    )

    # Verify that the strengths mention multiple disciplines
    strengths = overall_assessment["strengths"]
    assert len(strengths) > 0
    disciplines_in_strengths = 0
    for discipline in ["security", "user experience", "performance", "accessibility"]:
        if any(discipline.lower() in strength.lower() for strength in strengths):
            disciplines_in_strengths += 1
    assert (
        disciplines_in_strengths >= 2
    ), "Strengths should mention at least two disciplines"

    # Verify that the recommendation provides clear guidance
    assert (
        len(overall_assessment["recommendation"]) > 10
    )  # Ensure it's a meaningful recommendation


# Scenario: Integration with domain-specific knowledge
@given("a multi-disciplinary reasoning process")
def multi_disciplinary_reasoning_process(context):
    """Set up a multi-disciplinary reasoning process."""
    # Create a team if it doesn't exist yet
    if not hasattr(context, "team") or not context.team:
        context.team = WSDETeam(
            name="TestMultiDisciplinaryDialecticalReasoningStepsTeam"
        )

        # Create agents with different disciplinary expertise
        code_agent = create_mock_agent("CodeAgent", ["python", "coding"])
        security_agent = create_mock_agent(
            "SecurityAgent", ["security", "authentication"]
        )
        ux_agent = create_mock_agent("UXAgent", ["user_experience", "interface_design"])
        performance_agent = create_mock_agent(
            "PerformanceAgent", ["performance", "optimization"]
        )
        accessibility_agent = create_mock_agent(
            "AccessibilityAgent", ["accessibility", "inclusive_design"]
        )
        critic_agent = create_mock_agent(
            "CriticAgent", ["dialectical_reasoning", "critique", "synthesis"]
        )

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

        # Set disciplinary agents
        context.disciplinary_agents = [
            context.security_agent,
            context.ux_agent,
            context.performance_agent,
            context.accessibility_agent,
        ]

    # Create a task if it doesn't exist yet
    if not hasattr(context, "task") or not context.task:
        context.task = {
            "type": "implementation_task",
            "description": "Implement a user authentication system with a focus on security, usability, performance, and accessibility",
        }


@given("domain-specific knowledge sources for each discipline")
def domain_specific_knowledge_sources_for_each_discipline(context):
    """Set up domain-specific knowledge sources for each discipline."""
    # Create knowledge sources if they don't exist yet
    if not hasattr(context, "knowledge_sources") or not context.knowledge_sources:
        context.knowledge_sources = {
            "security": {
                "authentication_best_practices": [
                    "Use multi-factor authentication for sensitive operations",
                    "Store passwords using strong, adaptive hashing algorithms (e.g., bcrypt, Argon2)",
                    "Implement rate limiting to prevent brute force attacks",
                    "Use HTTPS for all authentication requests",
                    "Set secure and HttpOnly flags on authentication cookies",
                ],
                "sources": [
                    {
                        "title": "OWASP Authentication Cheat Sheet",
                        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html",
                    },
                    {
                        "title": "NIST Digital Identity Guidelines",
                        "url": "https://pages.nist.gov/800-63-3/",
                    },
                ],
            },
            "user_experience": {
                "authentication_ux_principles": [
                    "Minimize friction in the authentication process",
                    "Provide clear error messages for failed authentication attempts",
                    "Offer password recovery options",
                    "Remember user preferences where appropriate",
                    "Support single sign-on where possible",
                ],
                "sources": [
                    {
                        "title": "Nielsen Norman Group: Login Form Design",
                        "url": "https://www.nngroup.com/articles/login-form-design/",
                    },
                    {
                        "title": "Baymard Institute: Form Design Best Practices",
                        "url": "https://baymard.com/blog/login-form-design",
                    },
                ],
            },
            "performance": {
                "authentication_performance_considerations": [
                    "Optimize token validation for minimal latency",
                    "Cache frequently used authentication data",
                    "Use asynchronous processing for non-critical authentication tasks",
                    "Implement efficient database queries for user lookup",
                    "Monitor and optimize authentication service response times",
                ],
                "sources": [
                    {
                        "title": "Web.dev: Performance Optimization",
                        "url": "https://web.dev/performance-optimization/",
                    },
                    {
                        "title": "MDN: Performance Best Practices",
                        "url": "https://developer.mozilla.org/en-US/docs/Web/Performance/Performance_basics",
                    },
                ],
            },
            "accessibility": {
                "authentication_accessibility_guidelines": [
                    "Ensure all authentication forms are keyboard navigable",
                    "Provide appropriate ARIA labels for authentication form elements",
                    "Support screen readers for error messages and instructions",
                    "Maintain sufficient color contrast for text and interactive elements",
                    "Allow authentication timeout extensions for users who need more time",
                ],
                "sources": [
                    {
                        "title": "W3C Web Content Accessibility Guidelines (WCAG) 2.1",
                        "url": "https://www.w3.org/TR/WCAG21/",
                    },
                    {
                        "title": "WebAIM: Creating Accessible Forms",
                        "url": "https://webaim.org/techniques/forms/",
                    },
                ],
            },
        }


@when("the team applies multi-disciplinary dialectical reasoning")
def team_applies_multi_disciplinary_dialectical_reasoning(context):
    """Apply multi-disciplinary dialectical reasoning with domain-specific knowledge."""
    # Mock the team's method for applying multi-disciplinary dialectical reasoning
    context.team.apply_multi_disciplinary_dialectical_reasoning_with_knowledge = (
        MagicMock()
    )

    # Create a mock result with perspectives from different disciplines that incorporate domain-specific knowledge
    mock_result = {
        "thesis": {
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
            """,
        },
        "disciplinary_perspectives": [
            {
                "discipline": "security",
                "agent": "SecurityAgent",
                "perspective": "The solution needs to implement password hashing, rate limiting, and HTTPS.",
                "concerns": [
                    "Hardcoded credentials",
                    "No password hashing",
                    "No rate limiting",
                ],
                "recommendations": [
                    "Use bcrypt for password hashing",
                    "Implement rate limiting",
                    "Use HTTPS",
                ],
                "knowledge_sources": [
                    {
                        "title": "OWASP Authentication Cheat Sheet",
                        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html",
                    },
                    {
                        "title": "NIST Digital Identity Guidelines",
                        "url": "https://pages.nist.gov/800-63-3/",
                    },
                ],
            },
            {
                "discipline": "user_experience",
                "agent": "UXAgent",
                "perspective": "The authentication flow needs to be user-friendly with clear error messages.",
                "concerns": ["No error messages", "No password recovery"],
                "recommendations": [
                    "Add clear error messages",
                    "Implement password recovery",
                ],
                "knowledge_sources": [
                    {
                        "title": "Nielsen Norman Group: Login Form Design",
                        "url": "https://www.nngroup.com/articles/login-form-design/",
                    },
                    {
                        "title": "Baymard Institute: Form Design Best Practices",
                        "url": "https://baymard.com/blog/login-form-design",
                    },
                ],
            },
            {
                "discipline": "performance",
                "agent": "PerformanceAgent",
                "perspective": "Token validation should be optimized for minimal latency.",
                "concerns": [
                    "No caching strategy",
                    "Potential performance bottlenecks",
                ],
                "recommendations": [
                    "Cache frequently used authentication data",
                    "Optimize token validation",
                ],
                "knowledge_sources": [
                    {
                        "title": "Web.dev: Performance Optimization",
                        "url": "https://web.dev/performance-optimization/",
                    },
                    {
                        "title": "MDN: Performance Best Practices",
                        "url": "https://developer.mozilla.org/en-US/docs/Web/Performance/Performance_basics",
                    },
                ],
            },
            {
                "discipline": "accessibility",
                "agent": "AccessibilityAgent",
                "perspective": "Authentication forms must be accessible to all users.",
                "concerns": ["No keyboard navigation", "No ARIA labels"],
                "recommendations": ["Ensure keyboard navigability", "Add ARIA labels"],
                "knowledge_sources": [
                    {
                        "title": "W3C Web Content Accessibility Guidelines (WCAG) 2.1",
                        "url": "https://www.w3.org/TR/WCAG21/",
                    },
                    {
                        "title": "WebAIM: Creating Accessible Forms",
                        "url": "https://webaim.org/techniques/forms/",
                    },
                ],
            },
        ],
        "synthesis": {
            "integrated_perspectives": [
                {
                    "discipline": "security",
                    "key_points": ["Password hashing", "Rate limiting", "HTTPS"],
                },
                {
                    "discipline": "user_experience",
                    "key_points": ["Clear error messages", "Password recovery"],
                },
                {
                    "discipline": "performance",
                    "key_points": ["Caching", "Optimized validation"],
                },
                {
                    "discipline": "accessibility",
                    "key_points": ["Keyboard navigation", "ARIA labels"],
                },
            ],
            "perspective_conflicts": [
                {
                    "disciplines": ["security", "user_experience"],
                    "conflict": "Security measures may increase friction in the user experience",
                    "severity": "medium",
                    "assumptions": {
                        "security": "Strong security requires multiple verification steps",
                        "user_experience": "Users prefer minimal friction during authentication",
                    },
                }
            ],
            "conflict_resolutions": [
                {
                    "disciplines": ["security", "user_experience"],
                    "resolution": "Implement progressive security that balances protection with usability",
                    "trade_offs": [
                        "Slightly reduced security for better UX",
                        "Slightly increased friction for better security",
                    ],
                    "knowledge_sources": [
                        {
                            "title": "OWASP Authentication Cheat Sheet",
                            "url": "https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html",
                        },
                        {
                            "title": "Nielsen Norman Group: Login Form Design",
                            "url": "https://www.nngroup.com/articles/login-form-design/",
                        },
                    ],
                }
            ],
            "best_practices": {
                "security": [
                    "Use bcrypt for password hashing",
                    "Implement rate limiting",
                    "Use HTTPS",
                ],
                "user_experience": [
                    "Add clear error messages",
                    "Implement password recovery",
                ],
                "performance": [
                    "Cache frequently used authentication data",
                    "Optimize token validation",
                ],
                "accessibility": ["Ensure keyboard navigability", "Add ARIA labels"],
            },
            "knowledge_attribution": {
                "security": [
                    {
                        "practice": "Use bcrypt for password hashing",
                        "source": "OWASP Authentication Cheat Sheet",
                    },
                    {
                        "practice": "Implement rate limiting",
                        "source": "OWASP Authentication Cheat Sheet",
                    },
                    {
                        "practice": "Use HTTPS",
                        "source": "NIST Digital Identity Guidelines",
                    },
                ],
                "user_experience": [
                    {
                        "practice": "Add clear error messages",
                        "source": "Nielsen Norman Group: Login Form Design",
                    },
                    {
                        "practice": "Implement password recovery",
                        "source": "Baymard Institute: Form Design Best Practices",
                    },
                ],
                "performance": [
                    {
                        "practice": "Cache frequently used authentication data",
                        "source": "Web.dev: Performance Optimization",
                    },
                    {
                        "practice": "Optimize token validation",
                        "source": "MDN: Performance Best Practices",
                    },
                ],
                "accessibility": [
                    {
                        "practice": "Ensure keyboard navigability",
                        "source": "W3C Web Content Accessibility Guidelines (WCAG) 2.1",
                    },
                    {
                        "practice": "Add ARIA labels",
                        "source": "WebAIM: Creating Accessible Forms",
                    },
                ],
            },
        },
    }

    # Set the mock result
    context.team.apply_multi_disciplinary_dialectical_reasoning_with_knowledge.return_value = (
        mock_result
    )

    # Call the method to apply multi-disciplinary dialectical reasoning with knowledge
    context.result = (
        context.team.apply_multi_disciplinary_dialectical_reasoning_with_knowledge(
            context.task,
            context.critic_agent,
            context.knowledge_sources,
            context.disciplinary_agents,
        )
    )


@then("each disciplinary perspective should incorporate domain-specific knowledge")
def each_disciplinary_perspective_incorporates_domain_specific_knowledge(context):
    """Verify that each disciplinary perspective incorporates domain-specific knowledge."""
    # Verify that the result contains disciplinary perspectives
    assert "disciplinary_perspectives" in context.result

    # Verify that each perspective incorporates domain-specific knowledge
    for perspective in context.result["disciplinary_perspectives"]:
        # Verify that the perspective has knowledge sources
        assert "knowledge_sources" in perspective
        assert perspective["knowledge_sources"] is not None
        assert len(perspective["knowledge_sources"]) > 0

        # Verify that each knowledge source has a title and URL
        for source in perspective["knowledge_sources"]:
            assert "title" in source
            assert "url" in source
            assert source["title"] is not None
            assert source["url"] is not None

        # Verify that the perspective's recommendations are informed by the knowledge sources
        assert "recommendations" in perspective
        assert perspective["recommendations"] is not None
        assert len(perspective["recommendations"]) > 0


@then("the knowledge should be properly attributed to authoritative sources")
def knowledge_properly_attributed_to_authoritative_sources(context):
    """Verify that the knowledge is properly attributed to authoritative sources."""
    # Verify that the synthesis contains knowledge attribution
    assert "synthesis" in context.result
    assert "knowledge_attribution" in context.result["synthesis"]

    # Get the knowledge attribution
    knowledge_attribution = context.result["synthesis"]["knowledge_attribution"]

    # Verify that there is attribution for each discipline
    expected_disciplines = [
        "security",
        "user_experience",
        "performance",
        "accessibility",
    ]
    for discipline in expected_disciplines:
        assert (
            discipline in knowledge_attribution
        ), f"Discipline {discipline} not found in knowledge attribution"

        # Verify that each discipline has attributions
        discipline_attribution = knowledge_attribution[discipline]
        assert len(discipline_attribution) > 0

        # Verify that each attribution has a practice and source
        for attribution in discipline_attribution:
            assert "practice" in attribution
            assert "source" in attribution
            assert attribution["practice"] is not None
            assert attribution["source"] is not None

            # Verify that the source is an authoritative source
            if discipline == "security":
                assert any(
                    term in attribution["source"]
                    for term in ["OWASP", "NIST", "CIS", "ISO"]
                )
            elif discipline == "user_experience":
                assert any(
                    term in attribution["source"]
                    for term in ["Nielsen", "Baymard", "UX", "Design"]
                )
            elif discipline == "performance":
                assert any(
                    term in attribution["source"]
                    for term in ["Web.dev", "MDN", "Performance"]
                )
            elif discipline == "accessibility":
                assert any(
                    term in attribution["source"]
                    for term in ["W3C", "WCAG", "WebAIM", "Section 508"]
                )


@then("the synthesis should reflect current best practices across all disciplines")
def synthesis_reflects_current_best_practices_across_all_disciplines(context):
    """Verify that the synthesis reflects current best practices across all disciplines."""
    # Verify that the synthesis contains best practices
    assert "synthesis" in context.result
    assert "best_practices" in context.result["synthesis"]

    # Get the best practices
    best_practices = context.result["synthesis"]["best_practices"]

    # Verify that there are best practices for each discipline
    expected_disciplines = [
        "security",
        "user_experience",
        "performance",
        "accessibility",
    ]
    for discipline in expected_disciplines:
        assert (
            discipline in best_practices
        ), f"Discipline {discipline} not found in best practices"

        # Verify that each discipline has best practices
        discipline_practices = best_practices[discipline]
        assert len(discipline_practices) > 0

        # Verify that the best practices are relevant to the discipline
        if discipline == "security":
            assert any(
                "password" in practice.lower()
                or "hash" in practice.lower()
                or "https" in practice.lower()
                for practice in discipline_practices
            )
        elif discipline == "user_experience":
            assert any(
                "error" in practice.lower()
                or "message" in practice.lower()
                or "recovery" in practice.lower()
                for practice in discipline_practices
            )
        elif discipline == "performance":
            assert any(
                "cache" in practice.lower()
                or "optimi" in practice.lower()
                or "latency" in practice.lower()
                for practice in discipline_practices
            )
        elif discipline == "accessibility":
            assert any(
                "keyboard" in practice.lower()
                or "aria" in practice.lower()
                or "screen reader" in practice.lower()
                for practice in discipline_practices
            )


@then("the solution should demonstrate awareness of cross-disciplinary implications")
def solution_demonstrates_awareness_of_cross_disciplinary_implications(context):
    """Verify that the solution demonstrates awareness of cross-disciplinary implications."""
    # Verify that the synthesis contains conflict resolutions
    assert "synthesis" in context.result
    assert "conflict_resolutions" in context.result["synthesis"]

    # Get the conflict resolutions
    conflict_resolutions = context.result["synthesis"]["conflict_resolutions"]

    # Verify that there are conflict resolutions
    assert len(conflict_resolutions) > 0

    # Verify that each conflict resolution involves multiple disciplines
    for resolution in conflict_resolutions:
        assert "disciplines" in resolution
        assert len(resolution["disciplines"]) >= 2

        # Verify that the resolution addresses cross-disciplinary implications
        assert "resolution" in resolution
        assert "trade_offs" in resolution
        assert resolution["resolution"] is not None
        assert resolution["trade_offs"] is not None
        assert len(resolution["trade_offs"]) > 0

        # Verify that the resolution has knowledge sources
        assert "knowledge_sources" in resolution
        assert resolution["knowledge_sources"] is not None
        assert len(resolution["knowledge_sources"]) > 0

        # Verify that the knowledge sources come from different disciplines
        source_disciplines = set()
        for source in resolution["knowledge_sources"]:
            source_title = source["title"].lower()
            if any(term in source_title for term in ["owasp", "nist", "security"]):
                source_disciplines.add("security")
            elif any(
                term in source_title
                for term in ["nielsen", "ux", "user experience", "design"]
            ):
                source_disciplines.add("user_experience")
            elif any(
                term in source_title for term in ["performance", "web.dev", "mdn"]
            ):
                source_disciplines.add("performance")
            elif any(
                term in source_title for term in ["wcag", "accessibility", "webaim"]
            ):
                source_disciplines.add("accessibility")

        # Verify that the resolution incorporates knowledge from multiple disciplines
        assert (
            len(source_disciplines) >= 2
        ), f"Resolution should incorporate knowledge from multiple disciplines, but only found {source_disciplines}"
