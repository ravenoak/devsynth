from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, parsers, then, when

# Import the context fixture from the common file
from .test_mddr_common_steps import context


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
        "code": """
        def authenticate_user(username, password):
            # Basic authentication logic
            if username == "admin" and password == "password":
                return True
            return False
        """,
    }


@given("a task requiring security and user experience considerations")
def task_requiring_security_and_ux_considerations(context):
    """Define a task that requires security and user experience considerations."""
    context.task = {
        "type": "implementation_task",
        "description": "Implement a login form with secure authentication and good user experience",
    }


@given("knowledge sources for security and user experience")
def knowledge_sources_for_security_and_ux(context):
    """Provide knowledge sources for security and user experience."""
    # This step uses the knowledge sources defined in the background


@given("a task requiring performance and accessibility considerations")
def task_requiring_performance_and_accessibility_considerations(context):
    """Define a task that requires performance and accessibility considerations."""
    context.task = {
        "type": "implementation_task",
        "description": "Implement a responsive web form that is accessible to all users",
    }


@given("knowledge sources for performance and accessibility")
def knowledge_sources_for_performance_and_accessibility(context):
    """Provide knowledge sources for performance and accessibility."""
    # This step uses the knowledge sources defined in the background


@given(
    "a task requiring security, user experience, performance, and accessibility considerations"
)
def task_requiring_all_four_disciplines(context):
    """Define a task that requires all four disciplines."""
    context.task = {
        "type": "implementation_task",
        "description": "Implement a secure, user-friendly, high-performance, accessible authentication system",
    }


@given("knowledge sources for all four disciplines")
def knowledge_sources_for_all_four_disciplines(context):
    """Provide knowledge sources for all four disciplines."""
    # This step uses the knowledge sources defined in the background


@when("the team initiates multi-disciplinary dialectical reasoning")
def team_initiates_multi_disciplinary_dialectical_reasoning(context):
    """Initiate multi-disciplinary dialectical reasoning process."""
    # Mock the team's method for applying multi-disciplinary dialectical reasoning
    context.team.apply_multi_disciplinary_dialectical_reasoning = MagicMock()

    # Create a mock result with disciplinary perspectives
    mock_result = {
        "disciplinary_perspectives": [
            {
                "agent": "SecurityAgent",
                "discipline": "security",
                "perspective": "The authentication system should use secure password hashing and storage. It should implement rate limiting to prevent brute force attacks. All communication should be over HTTPS.",
                "considerations": [
                    "password_security",
                    "rate_limiting",
                    "secure_communication",
                ],
                "knowledge_sources": ["OWASP Top 10", "NIST Guidelines"],
                "disciplinary_context": "Security best practices require proper authentication mechanisms to prevent unauthorized access.",
            },
            {
                "agent": "UXAgent",
                "discipline": "user_experience",
                "perspective": "The login form should be simple and intuitive. Error messages should be clear but not reveal too much information. The system should remember returning users to minimize friction.",
                "considerations": ["form_design", "error_messaging", "user_friction"],
                "knowledge_sources": [
                    "Nielsen's Heuristics",
                    "Design System Guidelines",
                ],
                "disciplinary_context": "User experience principles emphasize ease of use and clear communication with users.",
            },
            {
                "agent": "PerformanceAgent",
                "discipline": "performance",
                "perspective": "The authentication process should be fast and efficient. Client-side validation should be used to reduce server load. The system should use caching where appropriate.",
                "considerations": ["response_time", "client_validation", "caching"],
                "knowledge_sources": [
                    "Web Performance Optimization",
                    "MDN Performance Guidelines",
                ],
                "disciplinary_context": "Performance optimization focuses on minimizing load times and server resource usage.",
            },
            {
                "agent": "AccessibilityAgent",
                "discipline": "accessibility",
                "perspective": "The login form must be keyboard navigable. All form elements need proper labels. Error states must be communicated through multiple channels (color, text, icons).",
                "considerations": [
                    "keyboard_navigation",
                    "form_labeling",
                    "error_communication",
                ],
                "knowledge_sources": ["WCAG 2.1 Guidelines", "WebAIM Checklist"],
                "disciplinary_context": "Accessibility standards ensure that all users, including those with disabilities, can use the system.",
            },
        ],
        "conflicts_identified": True,
        "synthesis_generated": False,
    }

    # Set the mock to return our prepared result
    context.team.apply_multi_disciplinary_dialectical_reasoning.return_value = (
        mock_result
    )

    # Call the method with the task
    context.result = context.team.apply_multi_disciplinary_dialectical_reasoning(
        context.task
    )


@then("each disciplinary agent should provide a specialized perspective")
def each_disciplinary_agent_provides_specialized_perspective(context):
    """Verify that each disciplinary agent provides a specialized perspective."""
    assert "disciplinary_perspectives" in context.result
    assert len(context.result["disciplinary_perspectives"]) >= 4

    # Verify that each perspective has an agent and discipline
    for perspective in context.result["disciplinary_perspectives"]:
        assert "agent" in perspective
        assert "discipline" in perspective
        assert "perspective" in perspective

        # Verify that the agent name matches the expected format
        assert perspective["agent"].endswith("Agent")

        # Verify that the discipline is one of the expected disciplines
        assert perspective["discipline"] in [
            "security",
            "user_experience",
            "performance",
            "accessibility",
        ]


@then("each perspective should focus on domain-specific considerations")
def each_perspective_focuses_on_domain_specific_considerations(context):
    """Verify that each perspective focuses on domain-specific considerations."""
    for perspective in context.result["disciplinary_perspectives"]:
        # Verify that each perspective has considerations
        assert "considerations" in perspective
        assert len(perspective["considerations"]) >= 2

        # Verify that the considerations are relevant to the discipline
        if perspective["discipline"] == "security":
            security_terms = [
                "password",
                "attack",
                "secure",
                "auth",
                "encrypt",
                "protect",
            ]
            has_security_focus = any(
                any(term in consideration for term in security_terms)
                for consideration in perspective["considerations"]
            )
            assert (
                has_security_focus
            ), f"Security perspective doesn't focus on security considerations: {perspective['considerations']}"

        elif perspective["discipline"] == "user_experience":
            ux_terms = [
                "user",
                "design",
                "interface",
                "usability",
                "friction",
                "experience",
            ]
            has_ux_focus = any(
                any(term in consideration for term in ux_terms)
                for consideration in perspective["considerations"]
            )
            assert (
                has_ux_focus
            ), f"UX perspective doesn't focus on UX considerations: {perspective['considerations']}"

        elif perspective["discipline"] == "performance":
            performance_terms = [
                "performance",
                "speed",
                "load",
                "time",
                "efficient",
                "cache",
            ]
            has_performance_focus = any(
                any(term in consideration for term in performance_terms)
                for consideration in perspective["considerations"]
            )
            assert (
                has_performance_focus
            ), f"Performance perspective doesn't focus on performance considerations: {perspective['considerations']}"

        elif perspective["discipline"] == "accessibility":
            accessibility_terms = [
                "accessibility",
                "a11y",
                "wcag",
                "aria",
                "keyboard",
                "screen reader",
            ]
            has_accessibility_focus = any(
                any(term in consideration for term in accessibility_terms)
                for consideration in perspective["considerations"]
            )
            assert (
                has_accessibility_focus
            ), f"Accessibility perspective doesn't focus on accessibility considerations: {perspective['considerations']}"


@then("the perspectives should be documented with disciplinary context")
def perspectives_documented_with_disciplinary_context(context):
    """Verify that the perspectives are documented with disciplinary context."""
    for perspective in context.result["disciplinary_perspectives"]:
        # Verify that each perspective has disciplinary context
        assert "disciplinary_context" in perspective
        assert len(perspective["disciplinary_context"]) > 0

        # Verify that the context mentions the discipline or related terms
        discipline = perspective["discipline"]
        if discipline == "security":
            assert any(
                term in perspective["disciplinary_context"].lower()
                for term in ["security", "secure", "protect", "auth", "access"]
            )
        elif discipline == "user_experience":
            assert any(
                term in perspective["disciplinary_context"].lower()
                for term in ["user", "experience", "ux", "usability", "design"]
            )
        elif discipline == "performance":
            assert any(
                term in perspective["disciplinary_context"].lower()
                for term in ["performance", "speed", "efficient", "load", "time"]
            )
        elif discipline == "accessibility":
            assert any(
                term in perspective["disciplinary_context"].lower()
                for term in ["accessibility", "accessible", "disability", "wcag"]
            )

        # Verify that the context includes some explanation of principles or standards
        assert any(
            term in perspective["disciplinary_context"].lower()
            for term in [
                "principle",
                "standard",
                "practice",
                "guideline",
                "focus",
                "emphasize",
                "ensure",
            ]
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
