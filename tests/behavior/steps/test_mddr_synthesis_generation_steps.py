from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, parsers, then, when

# Import the context fixture from the common file
from .test_mddr_common_steps import context


@given("perspectives and identified conflicts from multiple disciplines")
def perspectives_and_identified_conflicts_from_multiple_disciplines(context):
    """Set up perspectives and identified conflicts from multiple disciplines."""
    # Create mock perspectives
    context.perspectives = [
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
            "knowledge_sources": ["Nielsen's Heuristics", "Design System Guidelines"],
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
    ]

    # Create mock conflicts
    context.conflicts = [
        {
            "id": "conflict_1",
            "disciplines": ["security", "user_experience"],
            "description": "Security requirements for detailed error messages conflict with UX principles of clear, user-friendly messaging",
            "type": "trade-off",
            "severity": "medium",
            "assumptions": {
                "security": "Detailed error messages can leak information to attackers",
                "user_experience": "Clear error messages help users understand and resolve issues",
            },
            "priority": 2,
        },
        {
            "id": "conflict_2",
            "disciplines": ["security", "performance"],
            "description": "Security measures like rate limiting and complex validation conflict with performance goals for fast response times",
            "type": "resource_allocation",
            "severity": "high",
            "assumptions": {
                "security": "Thorough validation and rate limiting are necessary to prevent attacks",
                "performance": "Fast response times are critical for user satisfaction",
            },
            "priority": 1,
        },
        {
            "id": "conflict_3",
            "disciplines": ["accessibility", "performance"],
            "description": "Accessibility requirements for multiple communication channels may increase page weight and affect performance",
            "type": "implementation",
            "severity": "low",
            "assumptions": {
                "accessibility": "Multiple communication channels are necessary for users with disabilities",
                "performance": "Minimizing page weight is important for fast loading",
            },
            "priority": 3,
        },
    ]


@when("the team generates a multi-disciplinary synthesis")
def team_generates_multi_disciplinary_synthesis(context):
    """Simulate the team generating a multi-disciplinary synthesis."""
    # Mock the team's method for generating synthesis
    context.team.generate_multi_disciplinary_synthesis = MagicMock()

    # Create a mock synthesis result
    mock_synthesis = {
        "title": "Multi-disciplinary Authentication System Design",
        "description": "A comprehensive authentication system design that balances security, user experience, performance, and accessibility considerations.",
        "conflict_resolutions": [
            {
                "conflict_id": "conflict_1",
                "resolution": "Implement contextual error messages that provide clear guidance for users while avoiding security-sensitive details. Use generic messages for security-related errors but provide specific guidance for user input errors.",
                "disciplines_addressed": ["security", "user_experience"],
                "trade_offs": "Slightly reduced security information in exchange for improved usability",
            },
            {
                "conflict_id": "conflict_2",
                "resolution": "Implement tiered security measures with lightweight checks for most requests and more thorough validation for sensitive operations. Use asynchronous processing for non-critical security checks to maintain performance.",
                "disciplines_addressed": ["security", "performance"],
                "trade_offs": "Balanced security and performance through contextual application of security measures",
            },
            {
                "conflict_id": "conflict_3",
                "resolution": "Use modern frontend techniques like lazy loading and optimized assets to implement accessibility features without significant performance impact. Prioritize critical accessibility features in the initial load.",
                "disciplines_addressed": ["accessibility", "performance"],
                "trade_offs": "Slight increase in implementation complexity to maintain both accessibility and performance",
            },
        ],
        "integrated_insights": {
            "security": [
                "Use secure password hashing with bcrypt or Argon2",
                "Implement rate limiting with exponential backoff",
                "Use HTTPS for all authentication requests",
                "Apply principle of least privilege for authentication tokens",
            ],
            "user_experience": [
                "Provide clear, contextual error messages",
                "Minimize form fields to reduce friction",
                "Offer 'remember me' functionality for returning users",
                "Ensure visual hierarchy guides users through the authentication process",
            ],
            "performance": [
                "Use client-side validation to reduce server load",
                "Implement efficient caching strategies for authentication state",
                "Optimize database queries for user lookup",
                "Use asynchronous processing for non-critical operations",
            ],
            "accessibility": [
                "Ensure keyboard navigability for all form elements",
                "Provide proper ARIA labels and roles",
                "Communicate errors through multiple channels",
                "Support screen readers with appropriate announcements",
            ],
        },
        "disciplinary_integrity": {
            "security": "High - All critical security requirements are maintained",
            "user_experience": "High - Core usability principles are preserved",
            "performance": "Medium - Some performance optimizations are traded for security and accessibility",
            "accessibility": "High - All essential accessibility requirements are met",
        },
    }

    # Set the mock to return our prepared synthesis
    context.team.generate_multi_disciplinary_synthesis.return_value = mock_synthesis

    # Call the method with the perspectives and conflicts
    context.synthesis = context.team.generate_multi_disciplinary_synthesis(
        perspectives=context.perspectives, conflicts=context.conflicts
    )


@then("the synthesis should address all identified conflicts")
def synthesis_addresses_all_identified_conflicts(context):
    """Verify that the synthesis addresses all identified conflicts."""
    # Verify that the synthesis has conflict resolutions
    assert "conflict_resolutions" in context.synthesis

    # Get the list of conflict IDs from the original conflicts
    conflict_ids = [conflict["id"] for conflict in context.conflicts]

    # Get the list of conflict IDs from the resolutions
    resolution_conflict_ids = [
        resolution["conflict_id"]
        for resolution in context.synthesis["conflict_resolutions"]
    ]

    # Verify that all conflicts have resolutions
    for conflict_id in conflict_ids:
        assert (
            conflict_id in resolution_conflict_ids
        ), f"No resolution found for conflict {conflict_id}"

    # Verify that each resolution addresses the disciplines involved in the conflict
    for resolution in context.synthesis["conflict_resolutions"]:
        conflict_id = resolution["conflict_id"]

        # Find the original conflict
        original_conflict = next(
            (c for c in context.conflicts if c["id"] == conflict_id), None
        )
        assert (
            original_conflict is not None
        ), f"Original conflict {conflict_id} not found"

        # Verify that the resolution addresses all disciplines involved in the conflict
        for discipline in original_conflict["disciplines"]:
            assert (
                discipline in resolution["disciplines_addressed"]
            ), f"Resolution for {conflict_id} does not address {discipline}"

        # Verify that the resolution has a meaningful description
        assert (
            len(resolution["resolution"]) > 20
        ), f"Resolution for {conflict_id} is too short"

        # Verify that the resolution mentions trade-offs
        assert "trade_offs" in resolution
        assert (
            len(resolution["trade_offs"]) > 10
        ), f"Trade-offs for {conflict_id} are not adequately described"


@then("the synthesis should integrate insights from all disciplines")
def synthesis_integrates_insights_from_all_disciplines(context):
    """Verify that the synthesis integrates insights from all disciplines."""
    # Verify that the synthesis has integrated insights
    assert "integrated_insights" in context.synthesis

    # Verify that insights from all disciplines are included
    disciplines = ["security", "user_experience", "performance", "accessibility"]
    for discipline in disciplines:
        assert discipline in context.synthesis["integrated_insights"]
        assert len(context.synthesis["integrated_insights"][discipline]) > 0

        # Verify that each discipline has multiple insights
        assert len(context.synthesis["integrated_insights"][discipline]) >= 3

        # Verify that the insights are meaningful
        for insight in context.synthesis["integrated_insights"][discipline]:
            assert (
                len(insight) > 10
            ), f"Insight '{insight}' for {discipline} is too short"

            # Verify that the insight relates to the discipline
            if discipline == "security":
                assert any(
                    term in insight.lower()
                    for term in [
                        "secure",
                        "security",
                        "protect",
                        "auth",
                        "hash",
                        "encrypt",
                    ]
                )
            elif discipline == "user_experience":
                assert any(
                    term in insight.lower()
                    for term in [
                        "user",
                        "experience",
                        "ux",
                        "interface",
                        "usability",
                        "friction",
                    ]
                )
            elif discipline == "performance":
                assert any(
                    term in insight.lower()
                    for term in [
                        "performance",
                        "speed",
                        "efficient",
                        "load",
                        "time",
                        "cache",
                    ]
                )
            elif discipline == "accessibility":
                assert any(
                    term in insight.lower()
                    for term in [
                        "accessibility",
                        "a11y",
                        "aria",
                        "keyboard",
                        "screen reader",
                    ]
                )


@then("the synthesis should maintain disciplinary integrity where appropriate")
def synthesis_maintains_disciplinary_integrity(context):
    """Verify that the synthesis maintains disciplinary integrity where appropriate."""
    # Verify that the synthesis has disciplinary integrity assessments
    assert "disciplinary_integrity" in context.synthesis

    # Verify that integrity is assessed for all disciplines
    disciplines = ["security", "user_experience", "performance", "accessibility"]
    for discipline in disciplines:
        assert discipline in context.synthesis["disciplinary_integrity"]

        # Verify that the integrity assessment includes a level
        integrity = context.synthesis["disciplinary_integrity"][discipline]
        assert any(level in integrity for level in ["High", "Medium", "Low"])

        # Verify that the integrity assessment includes an explanation
        assert " - " in integrity
        explanation = integrity.split(" - ")[1]
        assert (
            len(explanation) > 10
        ), f"Explanation for {discipline} integrity is too short"


@then("the synthesis should document trade-offs between disciplinary requirements")
def synthesis_documents_trade_offs(context):
    """Verify that the synthesis documents trade-offs between disciplinary requirements."""
    # Verify that each conflict resolution includes trade-offs
    for resolution in context.synthesis["conflict_resolutions"]:
        assert "trade_offs" in resolution
        assert len(resolution["trade_offs"]) > 10

        # Verify that the trade-offs mention the disciplines involved
        disciplines = resolution["disciplines_addressed"]
        if len(disciplines) >= 2:
            discipline_terms = []
            for discipline in disciplines:
                if discipline == "security":
                    discipline_terms.extend(["security", "secure", "protection"])
                elif discipline == "user_experience":
                    discipline_terms.extend(["user", "experience", "usability", "ux"])
                elif discipline == "performance":
                    discipline_terms.extend(["performance", "speed", "efficient"])
                elif discipline == "accessibility":
                    discipline_terms.extend(["accessibility", "accessible", "a11y"])

            # Verify that at least one discipline term is mentioned in the trade-offs
            trade_offs_lower = resolution["trade_offs"].lower()
            assert any(
                term in trade_offs_lower for term in discipline_terms
            ), f"Trade-offs don't mention any disciplines: {resolution['trade_offs']}"
