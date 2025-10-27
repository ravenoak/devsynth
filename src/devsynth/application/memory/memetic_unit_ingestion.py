"""
Memetic Unit Ingestion Pipeline

This module provides the ingestion pipeline for transforming raw data into
structured Memetic Units with comprehensive metadata.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List
from uuid import uuid4

from ...domain.models.memory import (
    CognitiveType,
    MemeticMetadata,
    MemeticSource,
    MemeticStatus,
    MemeticUnit,
)
from ...logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class MemeticUnitIngestionPipeline:
    """Pipeline for transforming raw data into Memetic Units."""

    def __init__(self, embedding_provider=None, keyword_extractor=None):
        """Initialize the ingestion pipeline."""
        self.embedding_provider = embedding_provider
        self.keyword_extractor = keyword_extractor or self._default_keyword_extractor
        logger.info("Memetic Unit ingestion pipeline initialized")

    def process_raw_input(
        self,
        raw_data: Any,
        source: MemeticSource,
        context: Dict[str, Any] = None
    ) -> MemeticUnit:
        """Convert raw input into a properly annotated Memetic Unit."""
        # Generate unique ID and timestamps
        unit_id = uuid4()
        timestamp = self._get_current_timestamp()

        # Determine cognitive type based on content analysis
        cognitive_type = self._classify_cognitive_type(raw_data, source, context)

        # Generate semantic descriptors
        content_hash = self._compute_content_hash(raw_data)
        semantic_vector = self._generate_semantic_vector(raw_data)
        keywords = self._extract_keywords(raw_data)
        topic = self._classify_topic(raw_data, keywords)

        # Create comprehensive metadata
        metadata = MemeticMetadata(
            unit_id=unit_id,
            source=source,
            timestamp_created=timestamp,
            cognitive_type=cognitive_type,
            content_hash=content_hash,
            semantic_vector=semantic_vector,
            keywords=keywords,
            topic=topic,
            status=MemeticStatus.RAW,
            confidence_score=self._calculate_initial_confidence(raw_data, source),
            salience_score=self._calculate_initial_salience(context),
            access_control=self._determine_access_control(source, context)
        )

        # Create unit with payload
        unit = MemeticUnit(metadata=metadata, payload=raw_data)

        # Add contextual links if available
        if context:
            self._add_contextual_links(unit, context)

        logger.debug(f"Created Memetic Unit {unit_id} with cognitive type {cognitive_type.value}")
        return unit

    def _classify_cognitive_type(
        self,
        data: Any,
        source: MemeticSource,
        context: Dict
    ) -> CognitiveType:
        """Classify data into appropriate cognitive type."""
        # Agent interactions and current tasks -> WORKING
        if source in [MemeticSource.AGENT_SELF, MemeticSource.LLM_RESPONSE]:
            return CognitiveType.WORKING

        # Historical records and experiences -> EPISODIC
        if source in [
            MemeticSource.CODE_EXECUTION,
            MemeticSource.TEST_RESULT,
            MemeticSource.ERROR_LOG
        ]:
            return CognitiveType.EPISODIC

        # General knowledge and patterns -> SEMANTIC
        if source in [MemeticSource.DOCUMENTATION, MemeticSource.FILE_INGESTION]:
            return CognitiveType.SEMANTIC

        # Skills and executable procedures -> PROCEDURAL
        if source in [MemeticSource.API_RESPONSE] or "procedure" in str(data).lower():
            return CognitiveType.PROCEDURAL

        # Default to working memory for interactive content
        return CognitiveType.WORKING

    def _compute_content_hash(self, data: Any) -> str:
        """Generate consistent hash for content deduplication."""
        import hashlib
        import json

        # Normalize different data types
        if isinstance(data, (dict, list)):
            normalized = json.dumps(data, sort_keys=True, default=str)
        elif hasattr(data, '__dict__'):
            normalized = json.dumps(data.__dict__, sort_keys=True, default=str)
        else:
            normalized = str(data)

        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def _generate_semantic_vector(self, data: Any) -> List[float]:
        """Generate semantic embedding for content."""
        # This would integrate with embedding providers (OpenAI, LM Studio, etc.)
        # For now, return placeholder vector based on content hash
        import hashlib

        text_content = str(data)
        hash_obj = hashlib.md5(text_content.encode())
        hash_int = int(hash_obj.hexdigest(), 16)

        # Generate pseudo-random vector based on content hash
        vector = []
        for i in range(384):  # Common embedding dimension
            # Simple deterministic pseudo-random generation
            seed = hash_int + i * 31
            value = (seed * 1103515245 + 12345) & 0x7fffffff
            normalized = (value % 2000 - 1000) / 1000.0  # Scale to [-1, 1]
            vector.append(normalized)

        return vector

    def _default_keyword_extractor(self, data: Any) -> List[str]:
        """Extract meaningful keywords from content."""
        text = str(data).lower()

        # Remove code-like patterns and extract words
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.split()

        # Filter for meaningful words (length > 2, not common stop words)
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
            'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
            'those', 'a', 'an', 'as', 'if', 'when', 'where', 'why', 'how'
        }

        meaningful_words = [
            word for word in words
            if len(word) > 2 and word not in stop_words
        ]

        # Return top keywords (simplified)
        return meaningful_words[:10] if meaningful_words else ["general"]

    def _extract_keywords(self, data: Any) -> List[str]:
        """Extract keywords using configured extractor."""
        try:
            return self.keyword_extractor(data)
        except Exception as e:
            logger.warning(f"Keyword extraction failed: {e}")
            return self._default_keyword_extractor(data)

    def _classify_topic(self, data: Any, keywords: List[str]) -> str:
        """Classify content into high-level topic categories."""
        text = str(data).lower()

        # Topic classification rules based on content patterns
        topic_patterns = {
            'error_handling': ['error', 'exception', 'fail', 'bug', 'traceback', 'stack'],
            'testing': ['test', 'assert', 'verify', 'validate', 'unit', 'integration', 'bdd'],
            'code_structure': ['function', 'class', 'method', 'code', 'implementation', 'algorithm'],
            'requirements': ['require', 'spec', 'design', 'plan', 'feature', 'user', 'story'],
            'user_experience': ['user', 'interface', 'ui', 'experience', 'interaction', 'workflow'],
            'data_processing': ['data', 'database', 'query', 'model', 'schema', 'migration'],
            'configuration': ['config', 'setting', 'parameter', 'environment', 'deployment'],
            'documentation': ['doc', 'readme', 'guide', 'tutorial', 'example', 'reference']
        }

        for topic, patterns in topic_patterns.items():
            if any(pattern in text for pattern in patterns):
                return topic

        # Fallback to keyword-based classification
        if keywords:
            # Use most frequent or most specific keyword as topic
            primary_keyword = keywords[0]
            if any(word in primary_keyword for word in ['code', 'function', 'class']):
                return 'code_structure'
            elif any(word in primary_keyword for word in ['test', 'assert', 'verify']):
                return 'testing'
            elif any(word in primary_keyword for word in ['require', 'spec', 'design']):
                return 'requirements'
            else:
                return primary_keyword

        return 'general'

    def _calculate_initial_confidence(self, data: Any, source: MemeticSource) -> float:
        """Calculate initial confidence score for new content."""
        base_confidence = 0.7  # Default confidence

        # Adjust based on source reliability
        source_confidence = {
            MemeticSource.USER_INPUT: 0.8,
            MemeticSource.AGENT_SELF: 0.9,
            MemeticSource.LLM_RESPONSE: 0.7,
            MemeticSource.CODE_EXECUTION: 0.9,
            MemeticSource.TEST_RESULT: 0.8,
            MemeticSource.FILE_INGESTION: 0.6,
            MemeticSource.API_RESPONSE: 0.8,
            MemeticSource.ERROR_LOG: 0.9,
            MemeticSource.METRIC_DATA: 0.9,
            MemeticSource.CONFIGURATION: 0.8,
            MemeticSource.DOCUMENTATION: 0.7
        }

        source_bonus = source_confidence.get(source, 0.7)

        # Adjust based on content quality
        content_quality = self._assess_content_quality(data)
        quality_multiplier = 0.8 + (content_quality * 0.2)  # Range: 0.8-1.0

        return min(1.0, source_bonus * quality_multiplier)

    def _assess_content_quality(self, data: Any) -> float:
        """Assess quality of content for confidence calculation."""
        if not data:
            return 0.0

        quality_score = 0.0
        text_content = str(data)

        # Length-based quality (prefer substantial content)
        length_score = min(1.0, len(text_content) / 1000)  # Normalize to ~1000 chars
        quality_score += length_score * 0.4

        # Structure-based quality
        structure_indicators = 0
        if isinstance(data, dict) and len(data) > 3:
            structure_indicators += 0.3
        elif isinstance(data, list) and len(data) > 5:
            structure_indicators += 0.2
        elif '\n' in text_content or '.' in text_content:
            structure_indicators += 0.1

        quality_score += structure_indicators

        # Coherence-based quality (basic heuristic)
        words = text_content.split()
        if len(words) > 10:
            # Check for reasonable word lengths and variety
            avg_word_length = sum(len(word) for word in words) / len(words)
            if 3 <= avg_word_length <= 10:
                quality_score += 0.2

        return min(1.0, quality_score)

    def _calculate_initial_salience(self, context: Dict[str, Any]) -> float:
        """Calculate initial salience score based on context."""
        if not context:
            return 0.5  # Neutral salience

        # Context relevance factors
        relevance_score = 0.0

        # Recent activity context
        if "recent_activity" in context:
            relevance_score += 0.2

        # Current task context
        if "current_task" in context:
            relevance_score += 0.3

        # Agent state context
        if "agent_context" in context:
            relevance_score += 0.2

        return min(1.0, relevance_score)

    def _determine_access_control(self, source: MemeticSource, context: Dict[str, Any]) -> Dict[str, Any]:
        """Determine access control policy for the unit."""
        # Default permissive policy
        policy = {
            "read_access": "public",
            "write_access": "system",
            "retention_policy": "standard",
            "encryption_required": False
        }

        # Adjust based on source sensitivity
        if source in [MemeticSource.ERROR_LOG, MemeticSource.CONFIGURATION]:
            policy["read_access"] = "restricted"
            policy["encryption_required"] = True

        # Adjust based on context
        if context and "sensitive" in context:
            policy["read_access"] = "restricted"
            policy["encryption_required"] = True

        return policy

    def _add_contextual_links(self, unit: MemeticUnit, context: Dict[str, Any]) -> None:
        """Add contextual relationships to the unit."""
        # Link to parent context if available
        if "parent_unit_id" in context:
            try:
                parent_id = context["parent_unit_id"]
                unit.add_link(parent_id, "DERIVES_FROM", strength=0.8, context="parent_child")
            except (ValueError, TypeError):
                logger.warning(f"Invalid parent_unit_id in context: {parent_id}")

        # Link to related units if available
        if "related_unit_ids" in context:
            for related_id in context["related_unit_ids"]:
                try:
                    unit.add_link(related_id, "RELATED_TO", strength=0.6, context="semantic")
                except (ValueError, TypeError):
                    logger.warning(f"Invalid related_unit_id in context: {related_id}")

    def _get_current_timestamp(self):
        """Get current timestamp (can be overridden for testing)."""
        from datetime import datetime
        return datetime.now()

    def batch_process(self, raw_data_list: List[Any], source: MemeticSource, context: Dict[str, Any] = None) -> List[MemeticUnit]:
        """Process multiple items in batch for efficiency."""
        units = []
        for raw_data in raw_data_list:
            try:
                unit = self.process_raw_input(raw_data, source, context)
                units.append(unit)
            except Exception as e:
                logger.error(f"Failed to process raw data: {e}")
                # Continue processing other items
                continue

        logger.info(f"Batch processed {len(units)} Memetic Units")
        return units
