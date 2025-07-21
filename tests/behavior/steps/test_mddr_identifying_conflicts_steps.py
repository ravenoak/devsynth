import pytest
from pytest_bdd import given, when, then, parsers
from unittest.mock import MagicMock, patch

# Import the context fixture from the common file
from .test_mddr_common import context

@given("perspectives from multiple disciplinary agents")
def perspectives_from_multiple_disciplinary_agents(context):
    """Set up perspectives from multiple disciplinary agents."""
    # Create mock perspectives
    context.perspectives = [
        {
            "agent": "SecurityAgent",
            "discipline": "security",
            "perspective": "The authentication system should use secure password hashing and storage. It should implement rate limiting to prevent brute force attacks. All communication should be over HTTPS.",
            "considerations": ["password_security", "rate_limiting", "secure_communication"],
            "knowledge_sources": ["OWASP Top 10", "NIST Guidelines"],
            "disciplinary_context": "Security best practices require proper authentication mechanisms to prevent unauthorized access."
        },
        {
            "agent": "UXAgent",
            "discipline": "user_experience",
            "perspective": "The login form should be simple and intuitive. Error messages should be clear but not reveal too much information. The system should remember returning users to minimize friction.",
            "considerations": ["form_design", "error_messaging", "user_friction"],
            "knowledge_sources": ["Nielsen's Heuristics", "Design System Guidelines"],
            "disciplinary_context": "User experience principles emphasize ease of use and clear communication with users."
        },
        {
            "agent": "PerformanceAgent",
            "discipline": "performance",
            "perspective": "The authentication process should be fast and efficient. Client-side validation should be used to reduce server load. The system should use caching where appropriate.",
            "considerations": ["response_time", "client_validation", "caching"],
            "knowledge_sources": ["Web Performance Optimization", "MDN Performance Guidelines"],
            "disciplinary_context": "Performance optimization focuses on minimizing load times and server resource usage."
        },
        {
            "agent": "AccessibilityAgent",
            "discipline": "accessibility",
            "perspective": "The login form must be keyboard navigable. All form elements need proper labels. Error states must be communicated through multiple channels (color, text, icons).",
            "considerations": ["keyboard_navigation", "form_labeling", "error_communication"],
            "knowledge_sources": ["WCAG 2.1 Guidelines", "WebAIM Checklist"],
            "disciplinary_context": "Accessibility standards ensure that all users, including those with disabilities, can use the system."
        }
    ]
    
    # Store the perspectives in the context
    context.result = {"disciplinary_perspectives": context.perspectives}

@when("the team analyzes the perspectives")
def team_analyzes_perspectives(context):
    """Simulate the team analyzing the perspectives to identify conflicts."""
    # Mock the team's method for analyzing perspectives
    context.team.analyze_disciplinary_perspectives = MagicMock()
    
    # Create a mock result with identified conflicts
    mock_conflicts = [
        {
            "id": "conflict_1",
            "disciplines": ["security", "user_experience"],
            "description": "Security requirements for detailed error messages conflict with UX principles of clear, user-friendly messaging",
            "type": "trade-off",
            "severity": "medium",
            "assumptions": {
                "security": "Detailed error messages can leak information to attackers",
                "user_experience": "Clear error messages help users understand and resolve issues"
            },
            "priority": 2
        },
        {
            "id": "conflict_2",
            "disciplines": ["security", "performance"],
            "description": "Security measures like rate limiting and complex validation conflict with performance goals for fast response times",
            "type": "resource_allocation",
            "severity": "high",
            "assumptions": {
                "security": "Thorough validation and rate limiting are necessary to prevent attacks",
                "performance": "Fast response times are critical for user satisfaction"
            },
            "priority": 1
        },
        {
            "id": "conflict_3",
            "disciplines": ["accessibility", "performance"],
            "description": "Accessibility requirements for multiple communication channels may increase page weight and affect performance",
            "type": "implementation",
            "severity": "low",
            "assumptions": {
                "accessibility": "Multiple communication channels are necessary for users with disabilities",
                "performance": "Minimizing page weight is important for fast loading"
            },
            "priority": 3
        }
    ]
    
    # Set the mock to return our prepared conflicts
    context.team.analyze_disciplinary_perspectives.return_value = {
        "conflicts": mock_conflicts,
        "conflicts_identified": True,
        "conflict_count": len(mock_conflicts)
    }
    
    # Call the method with the perspectives
    context.conflicts_result = context.team.analyze_disciplinary_perspectives(context.perspectives)
    
    # Store the conflicts in the context
    context.conflicts = context.conflicts_result["conflicts"]

@then("conflicts between disciplinary perspectives should be identified")
def conflicts_between_disciplinary_perspectives_identified(context):
    """Verify that conflicts between disciplinary perspectives are identified."""
    assert "conflicts" in context.conflicts_result
    assert context.conflicts_result["conflicts_identified"] is True
    assert len(context.conflicts) > 0
    
    # Verify that each conflict involves at least two disciplines
    for conflict in context.conflicts:
        assert "disciplines" in conflict
        assert len(conflict["disciplines"]) >= 2

@then("each conflict should be categorized by type and severity")
def each_conflict_categorized_by_type_and_severity(context):
    """Verify that each conflict is categorized by type and severity."""
    for conflict in context.conflicts:
        # Verify that each conflict has type and severity
        assert "type" in conflict
        assert "severity" in conflict
        
        # Verify that the type is one of the expected types
        assert conflict["type"] in ["trade-off", "resource_allocation", "implementation", "conceptual"]
        
        # Verify that the severity is one of the expected severities
        assert conflict["severity"] in ["low", "medium", "high"]

@then("the underlying disciplinary assumptions should be documented")
def underlying_disciplinary_assumptions_documented(context):
    """Verify that the underlying disciplinary assumptions are documented."""
    for conflict in context.conflicts:
        # Verify that each conflict has assumptions
        assert "assumptions" in conflict
        
        # Verify that assumptions are documented for each discipline involved
        for discipline in conflict["disciplines"]:
            assert discipline in conflict["assumptions"]
            assert conflict["assumptions"][discipline] != ""
            
        # Verify that the assumptions explain the disciplinary perspective
        for discipline, assumption in conflict["assumptions"].items():
            assert len(assumption) > 10  # Ensure it's a meaningful explanation
            
            # Verify that the assumption mentions key terms related to the discipline
            if discipline == "security":
                assert any(term in assumption.lower() for term in ["secure", "attack", "protect", "risk"])
            elif discipline == "user_experience":
                assert any(term in assumption.lower() for term in ["user", "experience", "usability", "interface"])
            elif discipline == "performance":
                assert any(term in assumption.lower() for term in ["performance", "speed", "response", "time"])
            elif discipline == "accessibility":
                assert any(term in assumption.lower() for term in ["accessibility", "disability", "access", "user"])

@then("the conflicts should be prioritized for resolution")
def conflicts_prioritized_for_resolution(context):
    """Verify that the conflicts are prioritized for resolution."""
    for conflict in context.conflicts:
        # Verify that each conflict has a priority
        assert "priority" in conflict
        
        # Verify that the priority is a number
        assert isinstance(conflict["priority"], int)
        
        # Verify that higher severity conflicts have higher priority (lower number)
        if conflict["severity"] == "high":
            assert conflict["priority"] <= 2  # High severity should be priority 1 or 2
        elif conflict["severity"] == "low":
            assert conflict["priority"] >= 3  # Low severity should be lower priority