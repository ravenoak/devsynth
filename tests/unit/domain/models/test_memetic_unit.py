"""
Unit tests for Memetic Unit domain models.

This module tests the Memetic Unit abstraction functionality including
metadata management, cognitive classification, and lifecycle operations.
"""

from datetime import datetime, timedelta
from uuid import UUID

import pytest

from devsynth.domain.models.memory import (
    CognitiveType,
    MemeticLink,
    MemeticMetadata,
    MemeticSource,
    MemeticStatus,
    MemeticUnit,
)


class TestMemeticMetadata:
    """Test MemeticMetadata functionality."""

    def test_initialization(self):
        """Test MemeticMetadata initialization."""
        metadata = MemeticMetadata(
            source=MemeticSource.USER_INPUT, cognitive_type=CognitiveType.WORKING
        )

        assert metadata.unit_id is not None
        assert isinstance(metadata.unit_id, UUID)
        assert metadata.source == MemeticSource.USER_INPUT
        assert metadata.cognitive_type == CognitiveType.WORKING
        assert metadata.status == MemeticStatus.RAW
        assert metadata.confidence_score == 1.0
        assert metadata.salience_score == 0.5

    def test_serialization(self):
        """Test MemeticMetadata serialization."""
        metadata = MemeticMetadata(
            source=MemeticSource.CODE_EXECUTION,
            cognitive_type=CognitiveType.EPISODIC,
            confidence_score=0.8,
            salience_score=0.7,
        )

        metadata_dict = {
            "unit_id": str(metadata.unit_id),
            "source": metadata.source.value,
            "cognitive_type": metadata.cognitive_type.value,
            "status": metadata.status.value,
            "confidence_score": metadata.confidence_score,
            "salience_score": metadata.salience_score,
        }

        # Test that all fields are serializable
        assert metadata_dict["unit_id"] is not None
        assert metadata_dict["source"] == "code_execution"
        assert metadata_dict["cognitive_type"] == "episodic"


class TestMemeticUnit:
    """Test MemeticUnit functionality."""

    def test_creation(self):
        """Test MemeticUnit creation and initialization."""
        metadata = MemeticMetadata(
            source=MemeticSource.USER_INPUT, cognitive_type=CognitiveType.WORKING
        )
        payload = "Test user input content"

        unit = MemeticUnit(metadata=metadata, payload=payload)

        assert unit.metadata.unit_id is not None
        assert unit.payload == payload
        assert unit.metadata.timestamp_accessed is not None
        assert unit.metadata.access_count == 1
        assert unit.metadata.content_hash is not None

    def test_content_hash_generation(self):
        """Test content hash generation for different payload types."""
        # Test with string payload
        unit1 = MemeticUnit(
            metadata=MemeticMetadata(source=MemeticSource.USER_INPUT),
            payload="identical content",
        )

        unit2 = MemeticUnit(
            metadata=MemeticMetadata(source=MemeticSource.USER_INPUT),
            payload="identical content",
        )

        unit3 = MemeticUnit(
            metadata=MemeticMetadata(source=MemeticSource.USER_INPUT),
            payload="different content",
        )

        # Identical content should have identical hashes
        assert unit1.metadata.content_hash == unit2.metadata.content_hash

        # Different content should have different hashes
        assert unit1.metadata.content_hash != unit3.metadata.content_hash

    def test_serialization_roundtrip(self):
        """Test serialization and deserialization."""
        original_metadata = MemeticMetadata(
            source=MemeticSource.LLM_RESPONSE,
            cognitive_type=CognitiveType.SEMANTIC,
            confidence_score=0.9,
            salience_score=0.8,
        )

        original_unit = MemeticUnit(
            metadata=original_metadata, payload={"type": "test", "data": "sample"}
        )

        # Serialize
        unit_dict = original_unit.to_dict()

        # Deserialize
        reconstructed_unit = MemeticUnit.from_dict(unit_dict)

        # Verify roundtrip integrity
        assert str(reconstructed_unit.metadata.unit_id) == str(
            original_unit.metadata.unit_id
        )
        assert reconstructed_unit.metadata.source == original_unit.metadata.source
        assert (
            reconstructed_unit.metadata.cognitive_type
            == original_unit.metadata.cognitive_type
        )
        assert (
            reconstructed_unit.metadata.confidence_score
            == original_unit.metadata.confidence_score
        )
        assert (
            reconstructed_unit.metadata.salience_score
            == original_unit.metadata.salience_score
        )
        assert reconstructed_unit.payload == original_unit.payload

    def test_link_management(self):
        """Test relationship link management."""
        unit1 = MemeticUnit(
            metadata=MemeticMetadata(source=MemeticSource.USER_INPUT),
            payload="First unit",
        )

        unit2 = MemeticUnit(
            metadata=MemeticMetadata(source=MemeticSource.USER_INPUT),
            payload="Second unit",
        )

        # Add relationship
        unit1.add_link(
            unit2.metadata.unit_id,
            "RELATED_TO",
            strength=0.7,
            type="semantic",  # Put in metadata
        )

        assert len(unit1.metadata.links) == 1
        link = unit1.metadata.links[0]
        assert link.target_id == unit2.metadata.unit_id
        assert link.relationship_type == "RELATED_TO"
        assert link.strength == 0.7
        assert link.metadata["type"] == "semantic"

    def test_salience_update(self):
        """Test salience score updates based on context."""
        unit = MemeticUnit(
            metadata=MemeticMetadata(
                source=MemeticSource.USER_INPUT, salience_score=0.5
            ),
            payload="Test content",
        )

        # Update salience with relevant context
        context = {"current_task": "user_authentication", "recent_activity": True}

        unit.update_salience(context)

        # Salience should be updated (may increase or decrease)
        assert unit.metadata.salience_score >= 0.0
        assert unit.metadata.salience_score <= 1.0

    def test_lifecycle_management(self):
        """Test unit lifecycle and expiration."""
        # Create unit with lifespan policy
        metadata = MemeticMetadata(
            source=MemeticSource.USER_INPUT,
            lifespan_policy={"max_age_hours": 24, "max_inactive_hours": 12},
        )

        unit = MemeticUnit(metadata=metadata, payload="Test content")

        # Fresh unit should not be expired
        assert not unit.is_expired()

        # Test age and inactive time calculations
        assert unit.get_age_hours() >= 0
        assert unit.get_inactive_hours() >= 0

    def test_cognitive_type_properties(self):
        """Test cognitive type classification and properties."""
        # Test different cognitive types
        working_unit = MemeticUnit(
            metadata=MemeticMetadata(
                source=MemeticSource.USER_INPUT, cognitive_type=CognitiveType.WORKING
            ),
            payload="Current task context",
        )

        episodic_unit = MemeticUnit(
            metadata=MemeticMetadata(
                source=MemeticSource.CODE_EXECUTION,
                cognitive_type=CognitiveType.EPISODIC,
            ),
            payload="Execution result",
        )

        semantic_unit = MemeticUnit(
            metadata=MemeticMetadata(
                source=MemeticSource.DOCUMENTATION,
                cognitive_type=CognitiveType.SEMANTIC,
            ),
            payload="Knowledge documentation",
        )

        procedural_unit = MemeticUnit(
            metadata=MemeticMetadata(
                source=MemeticSource.API_RESPONSE,
                cognitive_type=CognitiveType.PROCEDURAL,
            ),
            payload="API procedure",
        )

        # Verify cognitive types are preserved
        assert working_unit.metadata.cognitive_type == CognitiveType.WORKING
        assert episodic_unit.metadata.cognitive_type == CognitiveType.EPISODIC
        assert semantic_unit.metadata.cognitive_type == CognitiveType.SEMANTIC
        assert procedural_unit.metadata.cognitive_type == CognitiveType.PROCEDURAL


class TestMemeticLink:
    """Test MemeticLink functionality."""

    def test_link_creation(self):
        """Test MemeticLink creation and properties."""
        target_id = UUID("12345678-1234-5678-9abc-def012345678")

        link = MemeticLink(
            target_id=target_id,
            relationship_type="IMPLEMENTS",
            strength=0.8,
            metadata={"validation_method": "semantic_similarity"},
        )

        assert link.target_id == target_id
        assert link.relationship_type == "IMPLEMENTS"
        assert link.strength == 0.8
        assert link.metadata["validation_method"] == "semantic_similarity"

    def test_link_serialization(self):
        """Test MemeticLink serialization."""
        link = MemeticLink(
            target_id=UUID("12345678-1234-5678-9abc-def012345678"),
            relationship_type="VALIDATES",
            strength=0.9,
        )

        link_dict = {
            "target_id": str(link.target_id),
            "relationship_type": link.relationship_type,
            "strength": link.strength,
            "metadata": link.metadata,
        }

        # Verify serialization structure
        assert link_dict["target_id"] == "12345678-1234-5678-9abc-def012345678"
        assert link_dict["relationship_type"] == "VALIDATES"
        assert link_dict["strength"] == 0.9
