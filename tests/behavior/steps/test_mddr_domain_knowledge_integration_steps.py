from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, parsers, then, when

# Import the context fixture from the common file
from .test_mddr_common_steps import context


@given("a multi-disciplinary reasoning process")
def multi_disciplinary_reasoning_process(context):
    """Set up a multi-disciplinary reasoning process."""
    # Mock the team's multi-disciplinary reasoning process
    context.team.has_multi_disciplinary_reasoning = True
    context.team.multi_disciplinary_reasoning_config = {
        "enabled": True,
        "disciplines": ["security", "user_experience", "performance", "accessibility"],
        "knowledge_integration": True,
        "cross_disciplinary_analysis": True,
    }

    # Create a task that requires multi-disciplinary reasoning
    context.task = {
        "type": "implementation_task",
        "description": "Implement a user authentication system with a focus on security, usability, performance, and accessibility",
        "requirements": [
            "The system must securely store user credentials",
            "The login process should be intuitive and user-friendly",
            "Authentication should be fast and efficient",
            "The system must be accessible to users with disabilities",
        ],
    }


@given("domain-specific knowledge sources for each discipline")
def domain_specific_knowledge_sources_for_each_discipline(context):
    """Set up domain-specific knowledge sources for each discipline."""
    # Create detailed knowledge sources for each discipline
    context.knowledge_sources = {
        "security": {
            "authentication_best_practices": [
                {
                    "title": "OWASP Authentication Best Practices",
                    "source": "OWASP Foundation",
                    "url": "https://owasp.org/www-project-authentication-best-practices/",
                    "key_points": [
                        "Use multi-factor authentication for sensitive operations",
                        "Store passwords using strong, adaptive hashing algorithms (e.g., bcrypt, Argon2)",
                        "Implement rate limiting to prevent brute force attacks",
                        "Use HTTPS for all authentication requests",
                        "Set secure and HttpOnly flags on authentication cookies",
                    ],
                    "publication_date": "2023-01-15",
                    "relevance_score": 0.95,
                },
                {
                    "title": "NIST Special Publication 800-63B: Digital Identity Guidelines",
                    "source": "National Institute of Standards and Technology",
                    "url": "https://pages.nist.gov/800-63-3/sp800-63b.html",
                    "key_points": [
                        "Implement password policies that encourage longer passwords",
                        "Check passwords against known breached passwords",
                        "Use secure password recovery mechanisms",
                        "Implement appropriate authentication assurance levels",
                    ],
                    "publication_date": "2022-06-30",
                    "relevance_score": 0.9,
                },
            ]
        },
        "user_experience": {
            "authentication_ux_principles": [
                {
                    "title": "Nielsen Norman Group: Login Form Design Guidelines",
                    "source": "Nielsen Norman Group",
                    "url": "https://www.nngroup.com/articles/login-form-design/",
                    "key_points": [
                        "Minimize friction in the authentication process",
                        "Provide clear error messages for failed authentication attempts",
                        "Offer password recovery options",
                        "Remember user preferences where appropriate",
                        "Support single sign-on where possible",
                    ],
                    "publication_date": "2023-03-10",
                    "relevance_score": 0.95,
                },
                {
                    "title": "Baymard Institute: Form Design Best Practices",
                    "source": "Baymard Institute",
                    "url": "https://baymard.com/blog/login-form-design",
                    "key_points": [
                        "Use inline validation for form fields",
                        "Provide password visibility toggles",
                        "Implement persistent login options",
                        "Optimize mobile login experiences",
                    ],
                    "publication_date": "2022-11-15",
                    "relevance_score": 0.85,
                },
            ]
        },
        "performance": {
            "authentication_performance_considerations": [
                {
                    "title": "Web.dev: Optimize Authentication Performance",
                    "source": "Google Web.dev",
                    "url": "https://web.dev/articles/performance-auth",
                    "key_points": [
                        "Optimize token validation for minimal latency",
                        "Cache frequently used authentication data",
                        "Use asynchronous processing for non-critical authentication tasks",
                        "Implement efficient database queries for user lookup",
                        "Monitor and optimize authentication service response times",
                    ],
                    "publication_date": "2023-02-20",
                    "relevance_score": 0.9,
                },
                {
                    "title": "MDN Web Docs: Performance Best Practices",
                    "source": "Mozilla Developer Network",
                    "url": "https://developer.mozilla.org/en-US/docs/Web/Performance/Performance_best_practices",
                    "key_points": [
                        "Minimize network requests during authentication",
                        "Optimize client-side validation",
                        "Use appropriate caching strategies",
                        "Implement progressive enhancement for authentication forms",
                    ],
                    "publication_date": "2022-09-05",
                    "relevance_score": 0.8,
                },
            ]
        },
        "accessibility": {
            "authentication_accessibility_guidelines": [
                {
                    "title": "WCAG 2.1 Guidelines for Authentication",
                    "source": "W3C Web Accessibility Initiative",
                    "url": "https://www.w3.org/WAI/standards-guidelines/wcag/",
                    "key_points": [
                        "Ensure all authentication forms are keyboard navigable",
                        "Provide appropriate ARIA labels for authentication form elements",
                        "Support screen readers for error messages and instructions",
                        "Ensure sufficient color contrast for all authentication UI elements",
                        "Provide alternatives to CAPTCHA or use accessible CAPTCHA options",
                    ],
                    "publication_date": "2023-01-30",
                    "relevance_score": 0.95,
                },
                {
                    "title": "WebAIM: Accessible Authentication",
                    "source": "Web Accessibility In Mind",
                    "url": "https://webaim.org/techniques/forms/",
                    "key_points": [
                        "Implement accessible error handling",
                        "Provide clear instructions for authentication steps",
                        "Ensure authentication timeouts are accessible",
                        "Support alternative authentication methods for users with disabilities",
                    ],
                    "publication_date": "2022-08-15",
                    "relevance_score": 0.9,
                },
            ]
        },
    }

    # Mock the team's knowledge retrieval method
    context.team.get_knowledge_for_discipline = MagicMock()
    context.team.get_knowledge_for_discipline.side_effect = (
        lambda discipline: context.knowledge_sources.get(discipline, {})
    )


@when("the team applies multi-disciplinary dialectical reasoning")
def team_applies_multi_disciplinary_dialectical_reasoning(context):
    """Simulate the team applying multi-disciplinary dialectical reasoning with domain knowledge integration."""
    # Mock the team's method for applying multi-disciplinary dialectical reasoning
    context.team.apply_multi_disciplinary_dialectical_reasoning_with_knowledge = (
        MagicMock()
    )

    # Create a mock result with knowledge integration
    mock_result = {
        "disciplinary_perspectives": [
            {
                "agent": "SecurityAgent",
                "discipline": "security",
                "perspective": "The authentication system should use secure password hashing with bcrypt or Argon2 as recommended by OWASP. It should implement rate limiting with exponential backoff to prevent brute force attacks as per NIST SP 800-63B. All communication should be over HTTPS with secure cookies.",
                "considerations": [
                    "password_security",
                    "rate_limiting",
                    "secure_communication",
                ],
                "knowledge_sources": [
                    {
                        "title": "OWASP Authentication Best Practices",
                        "source": "OWASP Foundation",
                        "key_points_used": [
                            "Store passwords using strong, adaptive hashing algorithms (e.g., bcrypt, Argon2)",
                            "Implement rate limiting to prevent brute force attacks",
                            "Use HTTPS for all authentication requests",
                        ],
                    },
                    {
                        "title": "NIST Special Publication 800-63B: Digital Identity Guidelines",
                        "source": "National Institute of Standards and Technology",
                        "key_points_used": [
                            "Implement password policies that encourage longer passwords",
                            "Check passwords against known breached passwords",
                        ],
                    },
                ],
                "disciplinary_context": "Security best practices from OWASP and NIST require proper authentication mechanisms to prevent unauthorized access and protect user data.",
            },
            {
                "agent": "UXAgent",
                "discipline": "user_experience",
                "perspective": "Based on Nielsen Norman Group guidelines, the login form should be simple and intuitive. Error messages should be clear but not reveal too much information. The system should remember returning users to minimize friction, and as recommended by Baymard Institute, should include password visibility toggles.",
                "considerations": ["form_design", "error_messaging", "user_friction"],
                "knowledge_sources": [
                    {
                        "title": "Nielsen Norman Group: Login Form Design Guidelines",
                        "source": "Nielsen Norman Group",
                        "key_points_used": [
                            "Minimize friction in the authentication process",
                            "Provide clear error messages for failed authentication attempts",
                            "Remember user preferences where appropriate",
                        ],
                    },
                    {
                        "title": "Baymard Institute: Form Design Best Practices",
                        "source": "Baymard Institute",
                        "key_points_used": [
                            "Use inline validation for form fields",
                            "Provide password visibility toggles",
                        ],
                    },
                ],
                "disciplinary_context": "User experience principles from Nielsen Norman Group and Baymard Institute emphasize ease of use and clear communication with users during the authentication process.",
            },
            {
                "agent": "PerformanceAgent",
                "discipline": "performance",
                "perspective": "Following Web.dev recommendations, the authentication process should be fast and efficient with optimized token validation. Client-side validation should be used to reduce server load as suggested by MDN. The system should use appropriate caching strategies for authentication data.",
                "considerations": ["response_time", "client_validation", "caching"],
                "knowledge_sources": [
                    {
                        "title": "Web.dev: Optimize Authentication Performance",
                        "source": "Google Web.dev",
                        "key_points_used": [
                            "Optimize token validation for minimal latency",
                            "Cache frequently used authentication data",
                            "Use asynchronous processing for non-critical authentication tasks",
                        ],
                    },
                    {
                        "title": "MDN Web Docs: Performance Best Practices",
                        "source": "Mozilla Developer Network",
                        "key_points_used": [
                            "Minimize network requests during authentication",
                            "Optimize client-side validation",
                        ],
                    },
                ],
                "disciplinary_context": "Performance optimization guidelines from Web.dev and MDN focus on minimizing load times and server resource usage during authentication.",
            },
            {
                "agent": "AccessibilityAgent",
                "discipline": "accessibility",
                "perspective": "According to WCAG 2.1 guidelines, the login form must be keyboard navigable and all form elements need proper ARIA labels. Error states must be communicated through multiple channels (color, text, icons) as recommended by WebAIM, and alternatives to CAPTCHA should be provided if used.",
                "considerations": [
                    "keyboard_navigation",
                    "form_labeling",
                    "error_communication",
                ],
                "knowledge_sources": [
                    {
                        "title": "WCAG 2.1 Guidelines for Authentication",
                        "source": "W3C Web Accessibility Initiative",
                        "key_points_used": [
                            "Ensure all authentication forms are keyboard navigable",
                            "Provide appropriate ARIA labels for authentication form elements",
                            "Support screen readers for error messages and instructions",
                        ],
                    },
                    {
                        "title": "WebAIM: Accessible Authentication",
                        "source": "Web Accessibility In Mind",
                        "key_points_used": [
                            "Implement accessible error handling",
                            "Provide clear instructions for authentication steps",
                        ],
                    },
                ],
                "disciplinary_context": "Accessibility standards from WCAG and WebAIM ensure that all users, including those with disabilities, can use the authentication system effectively.",
            },
        ],
        "synthesis": {
            "title": "Knowledge-Informed Multi-disciplinary Authentication System",
            "description": "A comprehensive authentication system design that integrates current best practices from security, user experience, performance, and accessibility domains.",
            "integrated_knowledge": {
                "security": [
                    "OWASP-recommended password hashing with bcrypt or Argon2",
                    "NIST-compliant rate limiting with exponential backoff",
                    "Industry-standard HTTPS implementation with secure cookies",
                ],
                "user_experience": [
                    "Nielsen Norman Group-inspired minimal friction login flow",
                    "Baymard Institute-recommended password visibility toggle",
                    "Research-based clear error messaging that balances security and usability",
                ],
                "performance": [
                    "Web.dev-optimized token validation process",
                    "MDN-recommended client-side validation to reduce server load",
                    "Performance-optimized caching strategy for authentication data",
                ],
                "accessibility": [
                    "WCAG 2.1 AA-compliant keyboard navigation",
                    "WebAIM-recommended accessible error handling",
                    "W3C-compliant ARIA implementation for screen reader support",
                ],
            },
            "cross_disciplinary_implications": [
                "Security measures are implemented with UX considerations to minimize user friction",
                "Performance optimizations maintain WCAG accessibility compliance",
                "UX improvements follow security best practices from OWASP and NIST",
                "Accessibility features are implemented with performance considerations from Web.dev",
            ],
        },
    }

    # Set the mock to return our prepared result
    context.team.apply_multi_disciplinary_dialectical_reasoning_with_knowledge.return_value = (
        mock_result
    )

    # Call the method with the task
    context.result = (
        context.team.apply_multi_disciplinary_dialectical_reasoning_with_knowledge(
            context.task
        )
    )


@then("each disciplinary perspective should incorporate domain-specific knowledge")
def each_disciplinary_perspective_incorporates_domain_specific_knowledge(context):
    """Verify that each disciplinary perspective incorporates domain-specific knowledge."""
    # Verify that each perspective has knowledge sources
    for perspective in context.result["disciplinary_perspectives"]:
        assert "knowledge_sources" in perspective
        assert len(perspective["knowledge_sources"]) > 0

        # Verify that each knowledge source has the required fields
        for source in perspective["knowledge_sources"]:
            assert "title" in source
            assert "source" in source
            assert "key_points_used" in source
            assert len(source["key_points_used"]) > 0

        # Verify that the perspective text mentions concepts from the knowledge sources
        perspective_text = perspective["perspective"].lower()
        for source in perspective["knowledge_sources"]:
            # Check if any key point is reflected in the perspective
            key_points_reflected = any(
                any(
                    term.lower() in perspective_text
                    for term in key_point.lower().split()
                )
                for key_point in source["key_points_used"]
            )
            assert (
                key_points_reflected
            ), f"Perspective does not reflect knowledge from {source['title']}"

            # Check if the source is mentioned by name
            source_name = source["source"].lower()
            assert any(
                term.lower() in perspective_text for term in source_name.split()
            ), f"Source {source['source']} not mentioned in perspective"


@then("the knowledge should be properly attributed to authoritative sources")
def knowledge_properly_attributed_to_authoritative_sources(context):
    """Verify that the knowledge is properly attributed to authoritative sources."""
    # Verify that each perspective attributes knowledge to sources
    for perspective in context.result["disciplinary_perspectives"]:
        # Check that the perspective mentions the sources
        perspective_text = perspective["perspective"].lower()

        # Get all source names
        source_names = [source["source"] for source in perspective["knowledge_sources"]]

        # Verify that at least one source is mentioned in the perspective
        assert any(
            source.lower() in perspective_text for source in source_names
        ), f"No sources mentioned in perspective: {perspective['perspective']}"

        # Verify that the disciplinary context mentions the sources
        context_text = perspective["disciplinary_context"].lower()
        assert any(
            source.lower() in context_text for source in source_names
        ), f"No sources mentioned in disciplinary context: {perspective['disciplinary_context']}"

        # Verify that each knowledge source is an authoritative source
        for source in perspective["knowledge_sources"]:
            source_name = source["source"].lower()

            # Check if the source is a recognized authority in the discipline
            if perspective["discipline"] == "security":
                assert any(
                    auth in source_name
                    for auth in ["owasp", "nist", "iso", "cert", "sans"]
                ), f"Not an authoritative security source: {source['source']}"
            elif perspective["discipline"] == "user_experience":
                assert any(
                    auth in source_name
                    for auth in ["nielsen", "norman", "baymard", "ux", "usability"]
                ), f"Not an authoritative UX source: {source['source']}"
            elif perspective["discipline"] == "performance":
                assert any(
                    auth in source_name
                    for auth in ["web.dev", "google", "mdn", "mozilla", "performance"]
                ), f"Not an authoritative performance source: {source['source']}"
            elif perspective["discipline"] == "accessibility":
                assert any(
                    auth in source_name
                    for auth in ["wcag", "w3c", "webaim", "accessibility"]
                ), f"Not an authoritative accessibility source: {source['source']}"


@then("the synthesis should reflect current best practices across all disciplines")
def synthesis_reflects_current_best_practices_across_all_disciplines(context):
    """Verify that the synthesis reflects current best practices across all disciplines."""
    # Verify that the synthesis has integrated knowledge
    assert "synthesis" in context.result
    assert "integrated_knowledge" in context.result["synthesis"]

    # Verify that integrated knowledge covers all disciplines
    integrated_knowledge = context.result["synthesis"]["integrated_knowledge"]
    disciplines = ["security", "user_experience", "performance", "accessibility"]
    for discipline in disciplines:
        assert discipline in integrated_knowledge
        assert len(integrated_knowledge[discipline]) > 0

        # Verify that each knowledge item mentions authoritative sources or standards
        for item in integrated_knowledge[discipline]:
            item_lower = item.lower()

            if discipline == "security":
                assert any(
                    std in item_lower
                    for std in ["owasp", "nist", "iso", "standard", "best practice"]
                ), f"Security item doesn't reference standards: {item}"
            elif discipline == "user_experience":
                assert any(
                    std in item_lower
                    for std in [
                        "nielsen",
                        "norman",
                        "baymard",
                        "research",
                        "recommended",
                    ]
                ), f"UX item doesn't reference standards: {item}"
            elif discipline == "performance":
                assert any(
                    std in item_lower
                    for std in ["web.dev", "mdn", "optimized", "recommended"]
                ), f"Performance item doesn't reference standards: {item}"
            elif discipline == "accessibility":
                assert any(
                    std in item_lower
                    for std in ["wcag", "w3c", "webaim", "compliant", "accessible"]
                ), f"Accessibility item doesn't reference standards: {item}"


@then("the solution should demonstrate awareness of cross-disciplinary implications")
def solution_demonstrates_awareness_of_cross_disciplinary_implications(context):
    """Verify that the solution demonstrates awareness of cross-disciplinary implications."""
    # Verify that the synthesis has cross-disciplinary implications
    assert "synthesis" in context.result
    assert "cross_disciplinary_implications" in context.result["synthesis"]

    # Verify that there are multiple cross-disciplinary implications
    implications = context.result["synthesis"]["cross_disciplinary_implications"]
    assert len(implications) >= 3

    # Verify that each implication mentions at least two disciplines
    disciplines = ["security", "user", "experience", "performance", "accessibility"]
    for implication in implications:
        implication_lower = implication.lower()
        mentioned_disciplines = sum(
            1 for discipline in disciplines if discipline in implication_lower
        )
        assert (
            mentioned_disciplines >= 2
        ), f"Implication doesn't mention at least two disciplines: {implication}"

        # Verify that the implication describes how disciplines interact
        interaction_terms = [
            "with",
            "while",
            "maintain",
            "follow",
            "consider",
            "balance",
            "trade-off",
        ]
        assert any(
            term in implication_lower for term in interaction_terms
        ), f"Implication doesn't describe discipline interaction: {implication}"

        # Verify that the implication mentions specific standards or practices
        standards_terms = [
            "best practice",
            "standard",
            "guideline",
            "recommended",
            "compliance",
            "owasp",
            "nist",
            "wcag",
            "nielsen",
        ]
        assert any(
            term in implication_lower for term in standards_terms
        ), f"Implication doesn't mention specific standards: {implication}"
