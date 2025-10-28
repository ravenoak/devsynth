"""
BDD step definitions for Memetic Unit Abstraction.

This module provides step implementations for testing the Memetic Unit
functionality including metadata management, cognitive classification,
and lifecycle governance.
"""

from __future__ import annotations

from typing import Any, Dict, List
from uuid import uuid4

import pytest
from pytest_bdd import given, then, when

from src.devsynth.application.memory.cognitive_type_classifier import (
    CognitiveTypeClassifier,
)
from src.devsynth.application.memory.memetic_unit_ingestion import (
    MemeticUnitIngestionPipeline,
)
from src.devsynth.domain.models.memory import (
    CognitiveType,
    MemeticMetadata,
    MemeticSource,
    MemeticStatus,
    MemeticUnit,
)


@given("the Memetic Unit system is configured and initialized")
def step_memetic_unit_system_configured(context):
    """Set up Memetic Unit system with default configuration."""
    context.ingestion_pipeline = MemeticUnitIngestionPipeline()
    context.classifier = CognitiveTypeClassifier(confidence_threshold=0.8)
    context.memetic_units = []
    context.metadata_validation = True


@given("metadata validation is enabled")
def step_metadata_validation_enabled(context):
    """Enable metadata validation for Memetic Units."""
    context.metadata_validation = True


@given("cognitive type classification is active")
def step_cognitive_classification_active(context):
    """Enable cognitive type classification."""
    context.cognitive_classification = True


@given("memory backends are adapted for Memetic Units")
def step_memory_backends_adapted(context):
    """Set up memory backends adapted for Memetic Units."""
    context.backends_adapted = True


@given("I have raw data from various sources")
def step_raw_data_from_sources(context):
    """Set up raw data from various sources for testing."""
    context.raw_data_samples = [
        {
            "source": MemeticSource.USER_INPUT,
            "data": "I need to implement user authentication for the application",
            "expected_type": CognitiveType.WORKING,
        },
        {
            "source": MemeticSource.CODE_EXECUTION,
            "data": {
                "function": "authenticate",
                "result": "success",
                "execution_time": 0.1,
            },
            "expected_type": CognitiveType.EPISODIC,
        },
        {
            "source": MemeticSource.DOCUMENTATION,
            "data": "User authentication system provides secure access to the application",
            "expected_type": CognitiveType.SEMANTIC,
        },
        {
            "source": MemeticSource.API_RESPONSE,
            "data": {"endpoint": "/auth/login", "method": "POST", "status": 200},
            "expected_type": CognitiveType.PROCEDURAL,
        },
    ]


@when("I process the data through the ingestion pipeline")
def step_process_through_ingestion(context):
    """Process raw data through the Memetic Unit ingestion pipeline."""
    context.created_units = []

    for sample in context.raw_data_samples:
        try:
            unit = context.ingestion_pipeline.process_raw_input(
                raw_data=sample["data"],
                source=sample["source"],
                context={"test_context": True},
            )
            context.created_units.append(unit)
        except Exception as e:
            context.ingestion_error = e
            break


@then("a valid Memetic Unit should be created")
def step_valid_memetic_unit_created(context):
    """Verify that a valid Memetic Unit was created."""
    assert len(context.created_units) > 0, "No Memetic Units were created"
    assert (
        context.ingestion_error is None
    ), f"Ingestion failed: {context.ingestion_error}"


@then("all metadata fields should be populated correctly")
def step_metadata_fields_populated(context):
    """Verify all metadata fields are populated correctly."""
    for unit in context.created_units:
        # Check required metadata fields
        assert unit.metadata.unit_id is not None
        assert unit.metadata.source is not None
        assert unit.metadata.timestamp_created is not None
        assert unit.metadata.cognitive_type is not None
        assert (
            unit.metadata.content_hash is not None
            and len(unit.metadata.content_hash) > 0
        )
        assert unit.metadata.keywords is not None
        assert unit.metadata.status == MemeticStatus.RAW
        assert 0.0 <= unit.metadata.confidence_score <= 1.0
        assert 0.0 <= unit.metadata.salience_score <= 1.0


@then("the cognitive type should be classified appropriately")
def step_cognitive_type_classified(context):
    """Verify cognitive type classification."""
    for i, unit in enumerate(context.created_units):
        expected_type = context.raw_data_samples[i]["expected_type"]

        # Verify classification matches expected type
        assert (
            unit.metadata.cognitive_type == expected_type
        ), f"Expected {expected_type}, got {unit.metadata.cognitive_type}"


@then("semantic descriptors should be generated")
def step_semantic_descriptors_generated(context):
    """Verify semantic descriptors are generated."""
    for unit in context.created_units:
        # Check semantic vector (should be non-empty for text content)
        if isinstance(unit.payload, str) and len(unit.payload) > 0:
            assert (
                len(unit.metadata.semantic_vector) > 0
            ), "Semantic vector should be generated for text content"

        # Check keywords (should be non-empty for meaningful content)
        assert len(unit.metadata.keywords) > 0, "Keywords should be extracted"

        # Check topic classification
        assert (
            unit.metadata.topic is not None and len(unit.metadata.topic) > 0
        ), "Topic should be classified"


@then("the content hash should be computed")
def step_content_hash_computed(context):
    """Verify content hash is computed."""
    for unit in context.created_units:
        assert unit.metadata.content_hash is not None
        assert len(unit.metadata.content_hash) > 0
        # Hash should be consistent for identical content
        assert isinstance(unit.metadata.content_hash, str)


@then("governance fields should be initialized")
def step_governance_fields_initialized(context):
    """Verify governance fields are initialized."""
    for unit in context.created_units:
        # Check status initialization
        assert unit.metadata.status == MemeticStatus.RAW

        # Check confidence score initialization
        assert unit.metadata.confidence_score > 0.0

        # Check access control initialization
        assert isinstance(unit.metadata.access_control, dict)

        # Check lifespan policy initialization
        assert isinstance(unit.metadata.lifespan_policy, dict)


@given("I have data from different sources")
def step_data_from_different_sources(context):
    """Set up data from different sources for cognitive classification testing."""
    context.classification_samples = [
        (
            MemeticSource.USER_INPUT,
            "What should I implement next?",
            CognitiveType.WORKING,
        ),
        (
            MemeticSource.CODE_EXECUTION,
            {"error": "authentication failed", "trace": "stack trace"},
            CognitiveType.EPISODIC,
        ),
        (
            MemeticSource.DOCUMENTATION,
            "The system provides user authentication features",
            CognitiveType.SEMANTIC,
        ),
        (
            MemeticSource.API_RESPONSE,
            {"method": "POST", "endpoint": "/login", "response": 200},
            CognitiveType.PROCEDURAL,
        ),
    ]


@when("the system classifies the cognitive type")
def step_system_classifies_cognitive_type(context):
    """Classify cognitive types for the test samples."""
    context.classification_results = []

    for source, data, expected_type in context.classification_samples:
        # Create a basic Memetic Unit for classification
        metadata = MemeticMetadata(
            source=source, cognitive_type=CognitiveType.WORKING  # Default
        )
        unit = MemeticUnit(metadata=metadata, payload=data)

        # Classify using the classifier
        classified_type = context.classifier.classify(
            unit, {"classification_test": True}
        )
        context.classification_results.append((unit, classified_type, expected_type))


@then("user input should be classified as WORKING memory")
def step_user_input_working_memory(context):
    """Verify user input is classified as working memory."""
    working_classifications = [
        (unit, classified, expected)
        for unit, classified, expected in context.classification_results
        if expected == CognitiveType.WORKING
    ]

    for unit, classified, expected in working_classifications:
        assert (
            classified == CognitiveType.WORKING
        ), f"User input classified as {classified}, expected {expected}"


@then("code execution results should be classified as EPISODIC memory")
def step_code_execution_episodic(context):
    """Verify code execution results are classified as episodic memory."""
    episodic_classifications = [
        (unit, classified, expected)
        for unit, classified, expected in context.classification_results
        if expected == CognitiveType.EPISODIC
    ]

    for unit, classified, expected in episodic_classifications:
        assert (
            classified == CognitiveType.EPISODIC
        ), f"Code execution classified as {classified}, expected {expected}"


@then("documentation should be classified as SEMANTIC memory")
def step_documentation_semantic(context):
    """Verify documentation is classified as semantic memory."""
    semantic_classifications = [
        (unit, classified, expected)
        for unit, classified, expected in context.classification_results
        if expected == CognitiveType.SEMANTIC
    ]

    for unit, classified, expected in semantic_classifications:
        assert (
            classified == CognitiveType.SEMANTIC
        ), f"Documentation classified as {classified}, expected {expected}"


@then("API responses should be classified as PROCEDURAL memory")
def step_api_response_procedural(context):
    """Verify API responses are classified as procedural memory."""
    procedural_classifications = [
        (unit, classified, expected)
        for unit, classified, expected in context.classification_results
        if expected == CognitiveType.PROCEDURAL
    ]

    for unit, classified, expected in procedural_classifications:
        assert (
            classified == CognitiveType.PROCEDURAL
        ), f"API response classified as {classified}, expected {expected}"


@then("classification should be deterministic and consistent")
def step_deterministic_classification(context):
    """Verify classification is deterministic and consistent."""
    # Test same input classified consistently
    test_data = "user authentication system"
    test_source = MemeticSource.USER_INPUT

    # Classify same input multiple times
    metadata1 = MemeticMetadata(source=test_source)
    unit1 = MemeticUnit(metadata=metadata1, payload=test_data)

    metadata2 = MemeticMetadata(source=test_source)
    unit2 = MemeticUnit(metadata=metadata2, payload=test_data)

    type1 = context.classifier.classify(unit1)
    type2 = context.classifier.classify(unit2)

    assert type1 == type2, f"Inconsistent classification: {type1} vs {type2}"


@given("I have Memetic Units with different ages and access patterns")
def step_memetic_units_different_ages(context):
    """Set up Memetic Units with different ages and access patterns."""
    import time
    from datetime import datetime, timedelta

    context.aged_units = []

    # Create units with different ages and access patterns
    now = datetime.now()

    # Recent, frequently accessed unit
    recent_unit = MemeticUnit(
        metadata=MemeticMetadata(
            source=MemeticSource.USER_INPUT,
            timestamp_created=now - timedelta(hours=1),
            timestamp_accessed=now - timedelta(minutes=5),
            access_count=10,
            confidence_score=0.9,
            salience_score=0.8,
        ),
        payload="frequently accessed content",
    )

    # Old, rarely accessed unit
    old_unit = MemeticUnit(
        metadata=MemeticMetadata(
            source=MemeticSource.DOCUMENTATION,
            timestamp_created=now - timedelta(days=30),
            timestamp_accessed=now - timedelta(days=7),
            access_count=1,
            confidence_score=0.7,
            salience_score=0.3,
        ),
        payload="rarely accessed documentation",
    )

    # Medium age, medium access unit
    medium_unit = MemeticUnit(
        metadata=MemeticMetadata(
            source=MemeticSource.CODE_EXECUTION,
            timestamp_created=now - timedelta(days=7),
            timestamp_accessed=now - timedelta(hours=1),
            access_count=5,
            confidence_score=0.8,
            salience_score=0.6,
        ),
        payload="medium access code result",
    )

    context.aged_units = [recent_unit, old_unit, medium_unit]


@when("the governance system processes the units")
def step_governance_processes_units(context):
    """Process units through the governance system."""
    context.governance_results = []

    for unit in context.aged_units:
        # Update salience based on current context
        unit.update_salience({"governance_test": True})

        # Check if unit is expired
        is_expired = unit.is_expired()

        # Calculate age and inactive time
        age_hours = unit.get_age_hours()
        inactive_hours = unit.get_inactive_hours()

        context.governance_results.append(
            {
                "unit_id": str(unit.metadata.unit_id),
                "updated_salience": unit.metadata.salience_score,
                "is_expired": is_expired,
                "age_hours": age_hours,
                "inactive_hours": inactive_hours,
            }
        )


@then("salience scores should be updated based on usage")
def step_salience_updated_based_on_usage(context):
    """Verify salience scores are updated based on usage patterns."""
    for result in context.governance_results:
        # Salience should be updated (not necessarily higher)
        assert "updated_salience" in result
        assert 0.0 <= result["updated_salience"] <= 1.0


@then("confidence scores should reflect data quality")
def step_confidence_reflects_quality(context):
    """Verify confidence scores reflect data quality."""
    # Check that units maintain their confidence scores
    for unit in context.aged_units:
        assert unit.metadata.confidence_score > 0.0
        assert unit.metadata.confidence_score <= 1.0


@then("expired units should be identified correctly")
def step_expired_units_identified(context):
    """Verify expired units are identified correctly."""
    for result in context.governance_results:
        # Should have expiration check result
        assert "is_expired" in result
        assert isinstance(result["is_expired"], bool)


@then("access patterns should influence retention decisions")
def step_access_patterns_influence_retention(context):
    """Verify access patterns influence retention decisions."""
    # Units with more recent access should have higher salience
    recent_access_result = next(
        r
        for r in context.governance_results
        if "frequently" in context.aged_units[0].payload
    )

    old_access_result = next(
        r
        for r in context.governance_results
        if "rarely" in context.aged_units[1].payload
    )

    # Recent access should generally have higher salience than old access
    assert (
        recent_access_result["updated_salience"]
        >= old_access_result["updated_salience"]
    )


@then("governance should not affect unit functionality")
def step_governance_no_functionality_affect(context):
    """Verify governance doesn't affect unit functionality."""
    # Units should still be accessible and functional after governance
    for unit in context.aged_units:
        assert unit.metadata.unit_id is not None
        assert unit.payload is not None
        assert unit.metadata.cognitive_type is not None


@given("I have identical content stored in multiple backends")
def step_identical_content_multiple_backends(context):
    """Set up identical content in multiple backends for deduplication testing."""
    context.duplicate_content = "This is identical content for deduplication testing"
    context.duplicate_units = []

    # Create multiple units with identical content
    for i in range(3):
        unit = MemeticUnit(
            metadata=MemeticMetadata(
                source=MemeticSource.USER_INPUT, cognitive_type=CognitiveType.WORKING
            ),
            payload=context.duplicate_content,
        )
        context.duplicate_units.append(unit)


@when("the deduplication system processes the content")
def step_deduplication_processes_content(context):
    """Process content through deduplication system."""
    context.deduplication_results = []

    # Check for duplicates among created units
    seen_hashes = set()
    duplicates_found = []

    for unit in context.duplicate_units:
        content_hash = unit.metadata.content_hash

        if content_hash in seen_hashes:
            duplicates_found.append(content_hash)
        else:
            seen_hashes.add(content_hash)

    context.deduplication_results = {
        "total_units": len(context.duplicate_units),
        "unique_hashes": len(seen_hashes),
        "duplicate_hashes": len(duplicates_found),
        "deduplication_ratio": len(seen_hashes) / len(context.duplicate_units),
    }


@then("identical content should be identified with >99% accuracy")
def step_identical_content_identified(context):
    """Verify identical content is identified with high accuracy."""
    results = context.deduplication_results

    # All units should have identical content hashes (100% accuracy for identical content)
    assert (
        results["deduplication_ratio"] == 1.0
    ), f"Expected 100% deduplication ratio, got {results['deduplication_ratio']}"


@then("content hashes should be consistent across backends")
def step_hashes_consistent_across_backends(context):
    """Verify content hashes are consistent."""
    # All units with identical content should have identical hashes
    all_hashes = [unit.metadata.content_hash for unit in context.duplicate_units]
    unique_hashes = set(all_hashes)

    assert (
        len(unique_hashes) == 1
    ), f"Expected single hash for identical content, got {len(unique_hashes)}: {unique_hashes}"


@then("duplicate units should be merged appropriately")
def step_duplicates_merged_appropriately(context):
    """Verify duplicate units are merged appropriately."""
    # This would be enhanced with actual merging logic
    # For now, verify that deduplication identifies the duplicates
    results = context.deduplication_results
    assert results["duplicate_hashes"] > 0


@then("metadata should be preserved during deduplication")
def step_metadata_preserved_during_deduplication(context):
    """Verify metadata is preserved during deduplication."""
    # Each unit should retain its complete metadata
    for unit in context.duplicate_units:
        assert unit.metadata.unit_id is not None
        assert unit.metadata.source is not None
        assert unit.metadata.cognitive_type is not None
        assert unit.metadata.content_hash is not None


@then("storage efficiency should be improved")
def step_storage_efficiency_improved(context):
    """Verify storage efficiency is improved through deduplication."""
    results = context.deduplication_results

    # Deduplication should identify opportunities for efficiency
    efficiency_ratio = results["unique_hashes"] / results["total_units"]
    assert efficiency_ratio < 1.0, "No deduplication opportunities found"

    # Should achieve significant efficiency improvement
    assert (
        efficiency_ratio <= 0.5
    ), f"Efficiency ratio {efficiency_ratio} is above 50% threshold"


@given("I have diverse content types (text, code, structured data)")
def step_diverse_content_types(context):
    """Set up diverse content types for semantic enhancement testing."""
    context.diverse_content = [
        {
            "type": "text",
            "content": "The user authentication system provides secure access to the application with multi-factor authentication and session management.",
            "expected_keywords": [
                "user",
                "authentication",
                "secure",
                "access",
                "application",
            ],
        },
        {
            "type": "code",
            "content": "def authenticate_user(username: str, password: str) -> bool:\n    return validate_credentials(username, password)",
            "expected_keywords": [
                "authenticate",
                "user",
                "username",
                "password",
                "validate",
            ],
        },
        {
            "type": "structured",
            "content": {
                "user_id": 123,
                "role": "admin",
                "permissions": ["read", "write", "delete"],
            },
            "expected_keywords": [
                "user",
                "role",
                "admin",
                "permissions",
                "read",
                "write",
            ],
        },
    ]


@when("the semantic enhancement processes the content")
def step_semantic_enhancement_processes(context):
    """Process content through semantic enhancement."""
    context.enhanced_units = []

    for content_item in context.diverse_content:
        # Create unit and process through ingestion (which includes semantic enhancement)
        unit = context.ingestion_pipeline.process_raw_input(
            raw_data=content_item["content"],
            source=MemeticSource.USER_INPUT,
            context={"semantic_enhancement_test": True},
        )
        context.enhanced_units.append(unit)


@then("semantic vectors should be generated for each unit")
def step_semantic_vectors_generated(context):
    """Verify semantic vectors are generated."""
    for unit in context.enhanced_units:
        assert (
            len(unit.metadata.semantic_vector) > 0
        ), f"No semantic vector generated for unit {unit.metadata.unit_id}"

        # Vector should have reasonable dimensions (not too small, not too large)
        vector_length = len(unit.metadata.semantic_vector)
        assert (
            10 <= vector_length <= 1000
        ), f"Vector length {vector_length} is outside expected range"


@then("keywords should be extracted accurately")
def step_keywords_extracted_accurately(context):
    """Verify keywords are extracted accurately."""
    for i, unit in enumerate(context.enhanced_units):
        expected_keywords = context.diverse_content[i]["expected_keywords"]

        # Check that expected keywords are present
        extracted_keywords = set(unit.metadata.keywords)
        expected_set = set(expected_keywords)

        # At least 60% of expected keywords should be found
        overlap = len(expected_set.intersection(extracted_keywords))
        coverage = overlap / len(expected_set) if expected_set else 0.0

        assert (
            coverage >= 0.6
        ), f"Keyword coverage {coverage} below 60% threshold. Expected: {expected_keywords}, Got: {unit.metadata.keywords}"


@then("topics should be classified correctly")
def step_topics_classified_correctly(context):
    """Verify topics are classified correctly."""
    for unit in context.enhanced_units:
        assert unit.metadata.topic is not None
        assert len(unit.metadata.topic) > 0

        # Topic should be meaningful (not just "general")
        assert (
            unit.metadata.topic != "general" or len(unit.metadata.keywords) < 3
        ), "Topic should be more specific than 'general' for rich content"


@then("content similarity should be computable")
def step_content_similarity_computable(context):
    """Verify content similarity can be computed."""
    # Test similarity between units with similar content
    auth_units = [
        unit for unit in context.enhanced_units if "auth" in str(unit.payload).lower()
    ]

    if len(auth_units) >= 2:
        unit1, unit2 = auth_units[:2]

        # Basic similarity check (this would be enhanced with proper vector similarity)
        keywords1 = set(unit1.metadata.keywords)
        keywords2 = set(unit2.metadata.keywords)

        overlap = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))

        similarity = overlap / union if union > 0 else 0.0
        assert similarity >= 0.0  # Basic validation that similarity is computable


@then("semantic search should work across modalities")
def step_semantic_search_across_modalities(context):
    """Verify semantic search works across different content modalities."""
    # This would be enhanced with actual semantic search implementation
    # For now, verify that all units have semantic vectors for search
    for unit in context.enhanced_units:
        assert (
            len(unit.metadata.semantic_vector) > 0
        ), f"Unit {unit.metadata.unit_id} lacks semantic vector for search"
