from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, parsers, then, when

# Import the context fixture from the common file
from .test_mddr_common_steps import context


@given("a synthesis generated from multi-disciplinary perspectives")
def synthesis_generated_from_multi_disciplinary_perspectives(context):
    """Set up a synthesis generated from multi-disciplinary perspectives."""
    # Create a mock synthesis
    context.synthesis = {
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


@when("the team evaluates the synthesis")
def team_evaluates_synthesis(context):
    """Simulate the team evaluating the synthesis."""
    # Mock the team's method for evaluating synthesis
    context.team.evaluate_multi_disciplinary_synthesis = MagicMock()

    # Create a mock evaluation result
    mock_evaluation = {
        "disciplinary_assessments": {
            "security": {
                "compliance_score": 0.9,
                "standards_compliance": {
                    "OWASP_Top_10": "Compliant",
                    "NIST_Guidelines": "Mostly Compliant",
                    "ISO_27001": "Partially Compliant",
                },
                "strengths": [
                    "Strong password security measures",
                    "Proper implementation of HTTPS",
                    "Effective rate limiting strategy",
                ],
                "concerns": [
                    "Generic error messages may slightly hinder troubleshooting of security issues"
                ],
                "overall_assessment": "The solution provides strong security measures while making reasonable trade-offs for usability.",
            },
            "user_experience": {
                "compliance_score": 0.95,
                "standards_compliance": {
                    "Nielsen_Heuristics": "Compliant",
                    "Design_System_Guidelines": "Compliant",
                },
                "strengths": [
                    "Clear and contextual error messages",
                    "Minimized form friction",
                    "Thoughtful user flow",
                ],
                "concerns": [
                    "Some security measures may add slight friction to the user experience"
                ],
                "overall_assessment": "The solution provides an excellent user experience while maintaining security.",
            },
            "performance": {
                "compliance_score": 0.8,
                "standards_compliance": {
                    "Web_Performance_Optimization": "Mostly Compliant",
                    "MDN_Performance_Guidelines": "Mostly Compliant",
                },
                "strengths": [
                    "Efficient client-side validation",
                    "Appropriate caching strategies",
                    "Asynchronous processing for non-critical operations",
                ],
                "concerns": [
                    "Security measures may impact response times for some operations",
                    "Accessibility features add some overhead to page weight",
                ],
                "overall_assessment": "The solution makes reasonable performance trade-offs to accommodate security and accessibility requirements.",
            },
            "accessibility": {
                "compliance_score": 0.9,
                "standards_compliance": {
                    "WCAG_2_1": "Compliant",
                    "WebAIM_Checklist": "Mostly Compliant",
                },
                "strengths": [
                    "Full keyboard navigability",
                    "Proper ARIA implementation",
                    "Multi-channel error communication",
                ],
                "concerns": [
                    "Some performance optimizations may slightly delay loading of non-critical accessibility features"
                ],
                "overall_assessment": "The solution provides excellent accessibility while balancing performance considerations.",
            },
        },
        "overall_quality_assessment": {
            "score": 0.88,
            "rating": "Excellent",
            "summary": "The solution successfully balances requirements across all four disciplines, with appropriate trade-offs where necessary. It maintains high standards in security, user experience, and accessibility while making reasonable compromises in performance.",
            "strengths": [
                "Comprehensive approach to balancing competing requirements",
                "Thoughtful resolution of cross-disciplinary conflicts",
                "Strong compliance with standards across all disciplines",
                "Clear documentation of trade-offs and their rationale",
            ],
            "improvement_opportunities": [
                "Further optimization of performance for security-critical operations",
                "More detailed guidance on implementation to ensure accessibility features don't impact performance",
                "Additional testing recommendations to verify cross-disciplinary effectiveness",
            ],
        },
    }

    # Set the mock to return our prepared evaluation
    context.team.evaluate_multi_disciplinary_synthesis.return_value = mock_evaluation

    # Call the method with the synthesis
    context.evaluation = context.team.evaluate_multi_disciplinary_synthesis(
        context.synthesis
    )


@then("the evaluation should assess the solution from each disciplinary perspective")
def evaluation_assesses_solution_from_each_disciplinary_perspective(context):
    """Verify that the evaluation assesses the solution from each disciplinary perspective."""
    # Verify that the evaluation has disciplinary assessments
    assert "disciplinary_assessments" in context.evaluation

    # Verify that assessments for all disciplines are included
    disciplines = ["security", "user_experience", "performance", "accessibility"]
    for discipline in disciplines:
        assert discipline in context.evaluation["disciplinary_assessments"]

        # Verify that each assessment has the required components
        assessment = context.evaluation["disciplinary_assessments"][discipline]
        assert "compliance_score" in assessment
        assert "strengths" in assessment
        assert "concerns" in assessment
        assert "overall_assessment" in assessment

        # Verify that the compliance score is a number between 0 and 1
        assert 0 <= assessment["compliance_score"] <= 1

        # Verify that strengths and concerns are non-empty lists
        assert len(assessment["strengths"]) > 0

        # Verify that the overall assessment is a meaningful statement
        assert len(assessment["overall_assessment"]) > 20


@then("the evaluation should verify compliance with discipline-specific standards")
def evaluation_verifies_compliance_with_discipline_specific_standards(context):
    """Verify that the evaluation checks compliance with discipline-specific standards."""
    # Verify that each disciplinary assessment includes standards compliance
    for discipline, assessment in context.evaluation[
        "disciplinary_assessments"
    ].items():
        assert "standards_compliance" in assessment
        assert len(assessment["standards_compliance"]) > 0

        # Verify that the standards are appropriate for the discipline
        standards = assessment["standards_compliance"].keys()
        if discipline == "security":
            security_standards = ["OWASP", "NIST", "ISO"]
            assert any(
                any(std in standard for std in security_standards)
                for standard in standards
            )
        elif discipline == "user_experience":
            ux_standards = ["Nielsen", "Heuristic", "Design", "UX"]
            assert any(
                any(std in standard for std in ux_standards) for standard in standards
            )
        elif discipline == "performance":
            performance_standards = ["Performance", "Web", "Speed", "MDN"]
            assert any(
                any(std in standard for std in performance_standards)
                for standard in standards
            )
        elif discipline == "accessibility":
            accessibility_standards = ["WCAG", "WebAIM", "A11y", "Accessibility"]
            assert any(
                any(std in standard for std in accessibility_standards)
                for standard in standards
            )

        # Verify that each standard has a compliance level
        for standard, compliance in assessment["standards_compliance"].items():
            assert compliance in [
                "Compliant",
                "Mostly Compliant",
                "Partially Compliant",
                "Non-Compliant",
            ]


@then("the evaluation should identify any remaining disciplinary concerns")
def evaluation_identifies_remaining_disciplinary_concerns(context):
    """Verify that the evaluation identifies any remaining disciplinary concerns."""
    # Verify that each disciplinary assessment includes concerns
    for discipline, assessment in context.evaluation[
        "disciplinary_assessments"
    ].items():
        assert "concerns" in assessment

        # If there are concerns, verify they are meaningful
        if assessment["concerns"]:
            for concern in assessment["concerns"]:
                assert len(concern) > 10

                # Verify that the concern relates to the discipline
                if discipline == "security":
                    assert any(
                        term in concern.lower()
                        for term in ["security", "secure", "protect", "risk", "attack"]
                    )
                elif discipline == "user_experience":
                    assert any(
                        term in concern.lower()
                        for term in [
                            "user",
                            "experience",
                            "usability",
                            "interface",
                            "friction",
                        ]
                    )
                elif discipline == "performance":
                    assert any(
                        term in concern.lower()
                        for term in ["performance", "speed", "response", "time", "load"]
                    )
                elif discipline == "accessibility":
                    assert any(
                        term in concern.lower()
                        for term in [
                            "accessibility",
                            "accessible",
                            "disability",
                            "wcag",
                            "aria",
                        ]
                    )


@then(
    "the evaluation should provide an overall assessment of multi-disciplinary quality"
)
def evaluation_provides_overall_assessment_of_multi_disciplinary_quality(context):
    """Verify that the evaluation provides an overall assessment of multi-disciplinary quality."""
    # Verify that the evaluation has an overall quality assessment
    assert "overall_quality_assessment" in context.evaluation

    # Verify that the overall assessment has the required components
    overall = context.evaluation["overall_quality_assessment"]
    assert "score" in overall
    assert "rating" in overall
    assert "summary" in overall
    assert "strengths" in overall
    assert "improvement_opportunities" in overall

    # Verify that the score is a number between 0 and 1
    assert 0 <= overall["score"] <= 1

    # Verify that the rating is one of the expected ratings
    assert overall["rating"] in [
        "Excellent",
        "Good",
        "Satisfactory",
        "Needs Improvement",
        "Poor",
    ]

    # Verify that the summary is a meaningful statement
    assert len(overall["summary"]) > 30

    # Verify that strengths and improvement opportunities are non-empty lists
    assert len(overall["strengths"]) > 0
    assert len(overall["improvement_opportunities"]) > 0

    # Verify that the summary mentions multiple disciplines
    disciplines = ["security", "user experience", "performance", "accessibility"]
    discipline_terms = [
        "security",
        "user",
        "experience",
        "performance",
        "accessibility",
    ]
    summary_lower = overall["summary"].lower()
    assert (
        sum(1 for term in discipline_terms if term in summary_lower) >= 3
    ), "Summary should mention at least 3 disciplines"
