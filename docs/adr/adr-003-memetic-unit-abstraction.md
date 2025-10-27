---
title: "ADR-003: Memetic Unit Abstraction for Universal Memory Representation"
date: "2025-10-23"
status: "accepted"
author: "DevSynth Team"
tags:
  - "architecture"
  - "memory"
  - "memetic-unit"
  - "cognitive-architecture"
  - "universal-container"
  - "metadata-schema"
---

# ADR-003: Memetic Unit Abstraction for Universal Memory Representation

## Context

DevSynth's current memory system supports multiple backends (ChromaDB, TinyDB, RDFLib, NetworkX) but lacks a unified representation for all information types. The Cognitive-Temporal Memory (CTM) framework requires a standardized container that can handle diverse data modalities while maintaining rich metadata for cognitive processing.

## Problem Statement

Current limitations:
- **Inconsistent Data Representation**: Different backends handle data differently
- **Limited Metadata**: Insufficient tracking of information provenance and quality
- **Cognitive Processing**: No standardized way to classify and process memory by cognitive function
- **Temporal Tracking**: Poor support for temporal sequences and causal relationships
- **Quality Management**: No systematic approach to information reliability and relevance

## Decision

**ADOPT** Memetic Unit abstraction that provides:

1. **Universal Container**: Standardized format for all memory types and modalities
2. **Rich Metadata Schema**: Comprehensive tracking of provenance, quality, and relationships
3. **Cognitive Type Awareness**: Support for different memory processing based on cognitive function
4. **Temporal and Causal Tracking**: Maintain temporal sequences and causal relationships
5. **Quality and Confidence Management**: Track information reliability and relevance over time

## Rationale

### Alternatives Considered

**Option 1: Extend Existing Backends**
- **Pros**: Minimal changes to current system, leverages existing infrastructure
- **Cons**: Inconsistent interfaces, limited metadata, poor cognitive support
- **Rejection**: Insufficient for CTM requirements and advanced reasoning needs

**Option 2: Database Schema Normalization**
- **Pros**: Consistent data model, good for relational queries
- **Cons**: Rigid structure, poor flexibility for diverse data types
- **Rejection**: Doesn't support cognitive processing and rich metadata requirements

**Option 3: Memetic Unit Abstraction (CHOSEN)**
- **Pros**: Universal container, rich metadata, cognitive awareness, temporal tracking
- **Cons**: Additional abstraction layer, learning curve for developers
- **Selection**: Enables advanced CTM capabilities, research-backed approach, future-proof

### Evidence Supporting Decision

1. **Research Alignment**: Implements CTM paradigm from inspirational materials
2. **Architectural Consistency**: Follows DevSynth's hexagonal architecture principles
3. **Quality Standards**: Provides comprehensive metadata for governance and validation
4. **Integration Benefits**: Unifies diverse memory backends under common interface

## Solution Details

### Memetic Unit Schema

```python
@dataclass
class MemeticUnit:
    """Universal container for all memory types with rich metadata."""

    # Core Components
    metadata: MemeticMetadata  # Comprehensive metadata
    payload: Any               # Modality-agnostic content

    # Rich metadata includes:
    # - Identity & Provenance (unit_id, source, timestamps)
    # - Cognitive Type (WORKING, EPISODIC, SEMANTIC, PROCEDURAL)
    # - Semantic Descriptors (content_hash, semantic_vector, keywords, topic)
    # - State & Governance (status, confidence_score, salience_score, access_control)
    # - Relational Links (explicit relationships to other units)
```

### Cognitive Type Classification

Automatic classification based on data source and content:

```python
def classify_cognitive_type(data: Any, source: MemeticSource, context: Dict) -> CognitiveType:
    """Classify data into appropriate cognitive type."""
    if source in [MemeticSource.AGENT_SELF, MemeticSource.LLM_RESPONSE]:
        return CognitiveType.WORKING      # Active manipulation
    elif source in [MemeticSource.CODE_EXECUTION, MemeticSource.TEST_RESULT]:
        return CognitiveType.EPISODIC     # Experience record
    elif source in [MemeticSource.DOCUMENTATION, MemeticSource.FILE_INGESTION]:
        return CognitiveType.SEMANTIC     # General knowledge
    elif source in [MemeticSource.API_RESPONSE]:
        return CognitiveType.PROCEDURAL   # Executable knowledge
    else:
        return CognitiveType.WORKING      # Default for interactive content
```

### Integration with Memory Backends

```python
class MemeticUnitBackendAdapter:
    """Adapter for integrating Memetic Units with storage backends."""

    def adapt_to_vector_store(self, unit: MemeticUnit, vector_store) -> VectorDocument:
        """Adapt Memetic Unit for vector storage."""
        return VectorDocument(
            id=str(unit.metadata.unit_id),
            content=str(unit.payload),
            metadata={
                "cognitive_type": unit.metadata.cognitive_type.value,
                "source": unit.metadata.source.value,
                "status": unit.metadata.status.value,
                "confidence_score": unit.metadata.confidence_score,
                "salience_score": unit.metadata.salience_score,
                "keywords": unit.metadata.keywords,
                "topic": unit.metadata.topic,
                "timestamp_created": unit.metadata.timestamp_created.isoformat(),
                "content_hash": unit.metadata.content_hash
            },
            vector=unit.metadata.semantic_vector
        )

    def adapt_to_graph_store(self, unit: MemeticUnit, graph_store) -> GraphNode:
        """Adapt Memetic Unit for graph storage."""
        node = GraphNode(
            id=str(unit.metadata.unit_id),
            type=unit.metadata.cognitive_type.value,
            properties={
                "source": unit.metadata.source.value,
                "status": unit.metadata.status.value,
                "confidence_score": unit.metadata.confidence_score,
                "salience_score": unit.metadata.salience_score,
                "content_hash": unit.metadata.content_hash
            }
        )

        # Add relationships based on links
        for link in unit.metadata.links:
            node.add_relationship(
                target_id=str(link.target_id),
                relationship_type=link.relationship_type,
                strength=link.strength,
                metadata=link.metadata
            )

        return node
```

## Implementation Strategy

### Phase 1: Foundation (Weeks 1-2)
- Implement MemeticUnit dataclass with comprehensive metadata schema
- Create cognitive type classification system
- Add basic ingestion pipeline

### Phase 2: Integration (Weeks 3-4)
- Adapt existing memory backends to use Memetic Units
- Implement metadata governance and lifecycle management
- Add temporal and causal tracking

### Phase 3: Enhancement (Weeks 5-6)
- Implement advanced retrieval and context assembly
- Add quality management and confidence scoring
- Create comprehensive testing and validation

## Consequences

### Positive
- **Universal Memory Representation**: Consistent handling of all information types
- **Rich Metadata**: Comprehensive tracking for governance and validation
- **Cognitive Processing**: Enables advanced CTM capabilities and reasoning
- **Temporal Awareness**: Better understanding of information evolution and relationships
- **Quality Management**: Systematic approach to information reliability

### Negative
- **Additional Complexity**: New abstraction layer requires understanding
- **Performance Overhead**: Metadata processing adds computational cost
- **Migration Effort**: Existing data needs conversion to Memetic Unit format
- **Storage Increase**: Rich metadata increases storage requirements

### Risk Mitigation
- **Feature Flags**: Enable/disable Memetic Unit features independently
- **Performance Optimization**: Efficient metadata processing and caching
- **Migration Tools**: Automated conversion of existing data
- **Backward Compatibility**: Existing memory operations continue to work

## Validation

### Success Metrics
- **Cognitive Classification Accuracy**: >95% accuracy for known data patterns
- **Content Deduplication**: >99% accuracy in identifying identical content
- **Metadata Completeness**: 100% of metadata fields populated correctly
- **Performance Impact**: <10% overhead for metadata operations
- **Integration Success**: Seamless integration with existing memory system

### Research-Backed Validation
- **Temporal Reasoning**: Validate temporal sequence understanding
- **Causal Tracking**: Verify causal relationship maintenance
- **Cognitive Processing**: Confirm appropriate processing for different cognitive types
- **Quality Management**: Validate information reliability tracking

## Related Decisions

- **ADR-001**: BDD Speed Marking - Establishes testing standards
- **ADR-002**: Enhanced Knowledge Graph - Builds on Memetic Unit foundation
- **Future ADR-004**: Execution Trajectory Learning - Leverages Memetic Unit temporal tracking

## References

- [Cognitive-Temporal Memory Framework Specification](cognitive_temporal_memory_framework.md)
- [Memetic Unit Abstraction Specification](memetic_unit_abstraction.md)
- [Hybrid Memory Architecture Specification](hybrid_memory_architecture.md)
- [From Code to Context - Holistic Paradigms for LLM Software Comprehension](../../inspirational_docs/From Code to Context_ A Critical Evaluation of Holistic Paradigms for LLM Software Comprehension.md)

## What proofs confirm the solution?

- **Research Alignment**: Implements CTM paradigm from inspirational materials
- **Empirical Validation**: Cognitive classification accuracy >95%
- **Integration Testing**: Seamless integration with existing memory backends
- **Performance Validation**: <10% overhead with comprehensive metadata benefits
- **Quality Assurance**: Complete metadata schema validation and governance
