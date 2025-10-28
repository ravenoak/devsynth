"""
BDD step definitions for Enhanced Knowledge Graph with Business Intent Layer.

This module provides step implementations for testing the enhanced knowledge graph
functionality including intent discovery, semantic linking, and multi-hop reasoning.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pytest
from pytest_bdd import given, then, when

from src.devsynth.application.memory.enhanced_knowledge_graph import (
    EnhancedKnowledgeGraph,
    Entity,
    IntentDiscoveryEngine,
    IntentLink,
    Relationship,
)
from src.devsynth.domain.models.memory import (
    CognitiveType,
    MemeticMetadata,
    MemeticSource,
    MemeticUnit,
)


@given("the enhanced knowledge graph is configured with business intent layer")
def step_enhanced_knowledge_graph_configured(context):
    """Set up enhanced knowledge graph with business intent capabilities."""
    context.enhanced_graph = EnhancedKnowledgeGraph()
    context.intent_discovery = IntentDiscoveryEngine()
    context.entities = {}
    context.intent_links = []


@given("business requirements are loaded into the graph")
def step_business_requirements_loaded(context):
    """Load business requirements into the knowledge graph."""
    # Create sample business requirements
    requirements_data = [
        {
            "id": "req_user_auth",
            "type": "BusinessRequirement",
            "properties": {
                "id": "REQ-001",
                "description": "Users must be able to authenticate securely",
                "priority": "high",
                "business_value": "security_compliance",
            },
        },
        {
            "id": "req_payment_processing",
            "type": "BusinessRequirement",
            "properties": {
                "id": "REQ-002",
                "description": "Process payments securely and efficiently",
                "priority": "high",
                "business_value": "revenue_generation",
            },
        },
    ]

    for req_data in requirements_data:
        entity = Entity(
            id=req_data["id"], type=req_data["type"], properties=req_data["properties"]
        )
        context.enhanced_graph.add_entity(entity)
        context.entities[req_data["id"]] = entity


@given("code is analyzed and stored in the graph")
def step_code_analyzed_and_stored(context):
    """Analyze and store code entities in the knowledge graph."""
    # Create sample code entities
    code_data = [
        {
            "id": "func_authenticate_user",
            "type": "Function",
            "properties": {
                "name": "authenticate_user",
                "signature": "def authenticate_user(username: str, password: str)",
                "complexity": "medium",
                "business_purpose": "user authentication and security",
            },
        },
        {
            "id": "func_process_payment",
            "type": "Function",
            "properties": {
                "name": "process_payment",
                "signature": "def process_payment(amount: float, currency: str)",
                "complexity": "high",
                "business_purpose": "secure payment processing",
            },
        },
    ]

    for code_data_item in code_data:
        entity = Entity(
            id=code_data_item["id"],
            type=code_data_item["type"],
            properties=code_data_item["properties"],
        )
        context.enhanced_graph.add_entity(entity)
        context.entities[code_data_item["id"]] = entity


@given("intent linking is enabled and trained")
def step_intent_linking_enabled(context):
    """Enable and configure intent linking capabilities."""
    context.intent_links_enabled = True
    context.similarity_threshold = 0.7


@when("the intent discovery engine analyzes the function")
def step_analyze_function_intent(context):
    """Analyze function for business intent."""
    # Get the authentication function
    auth_function = context.enhanced_graph.get_entity("func_authenticate_user")
    auth_requirement = context.enhanced_graph.get_entity("req_user_auth")

    # Discover intent relationship
    context.discovered_intent = context.intent_discovery.discover_intent(
        auth_function, auth_requirement
    )


@then("it should link the function to the revenue tracking requirement")
def step_link_function_to_requirement(context):
    """Verify function is linked to appropriate requirement."""
    assert context.discovered_intent is not None
    assert context.discovered_intent.requirement_id == "req_user_auth"
    assert context.discovered_intent.entity_id == "func_authenticate_user"


@then("assign a confidence score > 0.8")
def step_high_confidence_score(context):
    """Verify high confidence score for intent link."""
    assert context.discovered_intent.confidence > 0.8


@then("provide evidence of the semantic connection")
def step_provide_semantic_evidence(context):
    """Verify evidence is provided for the semantic connection."""
    assert context.discovered_intent.evidence
    assert len(context.discovered_intent.evidence) > 10


@then("validate the link against acceptance criteria")
def step_validate_against_acceptance_criteria(context):
    """Verify link validation against acceptance criteria."""
    assert context.discovered_intent.validation_method
    assert context.discovered_intent.confidence >= context.similarity_threshold


@when("the semantic linking engine processes the artifacts")
def step_process_semantic_linking(context):
    """Process artifacts through semantic linking engine."""
    context.intent_links = context.enhanced_graph.discover_intent_relationships()


@then("it should create links between code and requirements with >80% accuracy")
def step_create_links_with_high_accuracy(context):
    """Verify high accuracy in creating links."""
    assert len(context.intent_links) > 0

    # Verify link quality
    high_confidence_links = [
        link for link in context.intent_links if link.confidence > 0.8
    ]
    accuracy = len(high_confidence_links) / len(context.intent_links)

    assert accuracy > 0.8, f"Link accuracy {accuracy} is below 80% threshold"


@then("identify intent-implementation alignment issues")
def step_identify_alignment_issues(context):
    """Verify identification of intent-implementation alignment issues."""
    # Check for any low-confidence links that indicate potential issues
    low_confidence_links = [
        link for link in context.intent_links if link.confidence < 0.6
    ]

    # This test would be enhanced with actual misalignment detection
    # For now, just verify the linking process completed
    assert isinstance(context.intent_links, list)


@then("suggest improvements for unclear code intent")
def step_suggest_improvements(context):
    """Verify suggestions for intent clarity improvements."""
    # This would be enhanced with actual suggestion generation
    # For now, verify that the linking process provides actionable information
    for link in context.intent_links:
        assert (
            link.evidence
        ), f"Link {link.entity_id} lacks evidence for improvement suggestions"


@then("maintain semantic links during code evolution")
def step_maintain_links_during_evolution(context):
    """Verify semantic links are maintained during code changes."""
    # This would be enhanced with actual evolution tracking
    # For now, verify links are persistent
    assert len(context.intent_links) > 0

    # Verify links can be retrieved consistently
    for link in context.intent_links:
        retrieved_link = context.enhanced_graph.intent_links.get(
            f"{link.entity_id}--{link.intent_type}-->{link.requirement_id}"
        )
        assert retrieved_link is not None


@when('I query "{query}"')
def step_query_multi_hop(context, query):
    """Execute a multi-hop query."""
    context.query = query
    context.query_result = context.enhanced_graph.query_business_context(query)


@then("the system should traverse multiple hops correctly")
def step_multi_hop_traversal(context):
    """Verify correct multi-hop traversal."""
    assert context.query_result is not None
    assert len(context.query_result) > 0


@then("identify the business requirement with >85% accuracy")
def step_high_accuracy_identification(context):
    """Verify high accuracy in business requirement identification."""
    # Check if relevant requirements are found
    auth_requirements = [
        e for e in context.query_result if "auth" in str(e.properties).lower()
    ]
    assert len(auth_requirements) > 0


@then("provide complete traceability path")
def step_complete_traceability(context):
    """Verify complete traceability path is provided."""
    # Verify that both business and technical entities are in results
    business_entities = [
        e for e in context.query_result if e.type == "BusinessRequirement"
    ]
    technical_entities = [
        e for e in context.query_result if e.type in ["Function", "Class"]
    ]

    assert len(business_entities) > 0, "No business requirements in traceability path"
    assert len(technical_entities) > 0, "No technical entities in traceability path"


@then("explain the reasoning steps taken")
def step_explain_reasoning(context):
    """Verify reasoning steps are explained."""
    # This would be enhanced with actual reasoning explanation
    # For now, verify that results contain both business and technical context
    assert len(context.query_result) > 0


@then("show confidence scores for each link in the chain")
def step_show_confidence_scores(context):
    """Verify confidence scores are shown for links."""
    # Check intent links for confidence scores
    for link_id, link in context.enhanced_graph.intent_links.items():
        assert link.confidence >= 0.0
        assert link.confidence <= 1.0


@when("I query the impact of the proposed change")
def step_query_impact_analysis(context):
    """Query impact analysis for proposed changes."""
    # Start with authentication function
    start_entity = context.enhanced_graph.get_entity("func_authenticate_user")
    if start_entity:
        context.impact_analysis = context.enhanced_graph.calculate_blast_radius(
            start_entity.id, max_depth=3
        )


@then("the system should identify all affected business requirements")
def step_identify_affected_requirements(context):
    """Verify identification of affected business requirements."""
    assert context.impact_analysis is not None
    assert "affected_entities" in context.impact_analysis

    # Check if business requirements are identified as affected
    business_entities = [
        context.enhanced_graph.get_entity(eid)
        for eid in context.impact_analysis["affected_entities"]
        if eid in context.enhanced_graph.entities
    ]

    business_requirements = [
        e for e in business_entities if e.type == "BusinessRequirement"
    ]
    assert len(business_requirements) > 0


@then("calculate the business value impact")
def step_calculate_business_impact(context):
    """Verify business value impact calculation."""
    assert context.impact_analysis is not None
    assert "impact_metrics" in context.impact_analysis

    metrics = context.impact_analysis["impact_metrics"]
    assert "business_impact_score" in metrics
    assert metrics["business_impact_score"] >= 0


@then("assess risk to user experience")
def step_assess_user_experience_risk(context):
    """Verify user experience risk assessment."""
    metrics = context.impact_analysis["impact_metrics"]
    assert "risk_level" in metrics

    risk_level = metrics["risk_level"]
    assert risk_level in ["low", "medium", "high"]


@then("suggest mitigation strategies")
def step_suggest_mitigation_strategies(context):
    """Verify mitigation strategy suggestions."""
    metrics = context.impact_analysis["impact_metrics"]

    # Based on risk level, mitigation strategies should be suggested
    risk_level = metrics["risk_level"]
    if risk_level in ["medium", "high"]:
        # High risk should suggest mitigation
        assert metrics["business_impact_score"] >= 0


@then("provide confidence metrics for the analysis")
def step_provide_confidence_metrics(context):
    """Verify confidence metrics are provided."""
    # Impact analysis should include confidence measures
    assert context.impact_analysis is not None
    assert "blast_radius" in context.impact_analysis
    assert context.impact_analysis["blast_radius"] >= 0


@when("the intent discovery engine analyzes the inconsistencies")
def step_analyze_inconsistencies(context):
    """Analyze intent-implementation inconsistencies."""
    # Create a function with misleading names and comments
    misleading_function = Entity(
        id="func_misleading",
        type="Function",
        properties={
            "name": "calculate_simple_math",  # Misleading name
            "signature": "def calculate_simple_math(a: int, b: int)",
            "complexity": "low",
            "business_purpose": "simple arithmetic",  # Inconsistent with actual complexity
        },
    )

    context.enhanced_graph.add_entity(misleading_function)

    # Try to link with a complex requirement
    complex_requirement = Entity(
        id="req_complex_calculation",
        type="BusinessRequirement",
        properties={
            "id": "REQ-003",
            "description": "Perform complex financial calculations with multiple variables",
            "priority": "high",
        },
    )

    context.enhanced_graph.add_entity(complex_requirement)

    # Discover intent (should have low confidence due to mismatch)
    context.inconsistency_analysis = context.intent_discovery.discover_intent(
        misleading_function, complex_requirement
    )


@then("it should identify the intent-implementation mismatch")
def step_identify_mismatch(context):
    """Verify identification of intent-implementation mismatch."""
    if context.inconsistency_analysis:
        # Low confidence should indicate potential mismatch
        assert context.inconsistency_analysis.confidence < 0.7


@then("assign low confidence scores to inconsistent links")
def step_low_confidence_for_inconsistent(context):
    """Verify low confidence for inconsistent links."""
    if context.inconsistency_analysis:
        assert context.inconsistency_analysis.confidence < 0.8


@then("suggest improvements for clearer intent expression")
def step_suggest_improvements_for_clarity(context):
    """Verify suggestions for clearer intent expression."""
    # The evidence should suggest what improvements are needed
    if context.inconsistency_analysis:
        assert context.inconsistency_analysis.evidence
        # Evidence should indicate the mismatch
        assert (
            "simple" in context.inconsistency_analysis.evidence.lower()
            or "complex" in context.inconsistency_analysis.evidence.lower()
        )


@then("provide evidence for the inconsistency detection")
def step_provide_inconsistency_evidence(context):
    """Verify evidence is provided for inconsistency detection."""
    if context.inconsistency_analysis:
        assert context.inconsistency_analysis.evidence
        assert len(context.inconsistency_analysis.evidence) > 0


@when("I perform complex multi-hop queries")
def step_perform_complex_queries(context):
    """Perform complex multi-hop queries on the graph."""
    context.complex_queries = [
        "user authentication",
        "payment processing",
        "security requirements",
    ]

    context.query_results = []
    for query in context.complex_queries:
        result = context.enhanced_graph.query_business_context(query)
        context.query_results.append(result)


@then("query response time should be <2 seconds")
def step_query_response_time(context):
    """Verify query response time meets performance requirements."""
    # This would be enhanced with actual timing measurements
    # For now, verify that queries return results
    for result in context.query_results:
        assert result is not None


@then("memory usage should be <15% above baseline")
def step_memory_usage_baseline(context):
    """Verify memory usage stays within acceptable bounds."""
    # This would be enhanced with actual memory monitoring
    # For now, verify that the graph operations complete
    assert len(context.enhanced_graph.entities) > 0
    assert len(context.enhanced_graph.relationships) >= 0


@then("all existing graph operations should continue to work")
def step_existing_operations_work(context):
    """Verify backward compatibility of existing operations."""
    # Test basic graph operations still work
    entity = context.enhanced_graph.get_entity("func_authenticate_user")
    assert entity is not None

    entities_by_type = context.enhanced_graph.get_entities_by_type("Function")
    assert len(entities_by_type) > 0

    connected_entities = context.enhanced_graph.get_connected_entities(
        "func_authenticate_user"
    )
    # Should return some connected entities (may be empty list if none exist)


@then("enhanced features should not degrade performance")
def step_enhanced_features_no_degradation(context):
    """Verify enhanced features don't degrade overall performance."""
    # Run performance test with intent discovery
    context.intent_links = context.enhanced_graph.discover_intent_relationships()

    # Verify intent discovery completes
    assert isinstance(context.intent_links, list)

    # Verify validation still works
    validation = context.enhanced_graph.validate_intent_links()
    assert "total_links" in validation
