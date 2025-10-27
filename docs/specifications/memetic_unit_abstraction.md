---
title: "Memetic Unit Abstraction for Universal Memory Representation"
date: "2025-10-23"
version: "0.1.0-alpha.1"
tags:
  - "specification"
  - "memory"
  - "memetic-unit"
  - "cognitive-architecture"
  - "universal-container"
  - "metadata-schema"

status: "published"
author: "DevSynth Team"
last_reviewed: "2025-10-23"
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Specifications</a> &gt; Memetic Unit Abstraction
</div>

# Memetic Unit Abstraction for Universal Memory Representation

## 1. Overview

This specification defines the Memetic Unit abstraction for DevSynth's memory system, providing a universal, metadata-rich container for all forms of information throughout the software development lifecycle. The Memetic Unit serves as the foundational building block for the enhanced Cognitive-Temporal Memory (CTM) framework, enabling sophisticated memory management and reasoning capabilities.

## 2. Purpose and Goals

The Memetic Unit abstraction aims to:

1. **Universal Information Container**: Provide a standardized format for all memory types and modalities
2. **Rich Metadata Schema**: Enable comprehensive tracking of information provenance, quality, and relationships
3. **Cognitive Type Awareness**: Support different memory processing based on cognitive function
4. **Temporal and Causal Tracking**: Maintain temporal sequences and causal relationships
5. **Quality and Confidence Management**: Track information reliability and relevance over time
6. **Cross-Modal Integration**: Seamlessly handle text, code, structured data, and other modalities

## 3. Core Philosophy

### 3.1 Memory as a Managed Resource

The Memetic Unit paradigm treats memory as a comprehensive operating system analogous to MemOS, actively governing the entire information lifecycle:

- **Ingestion & Annotation**: Transform raw data into structured, traceable Memetic Units
- **Consolidation & Abstraction**: Extract patterns and create higher-level knowledge
- **Retrieval & Context Assembly**: Provide optimal context for reasoning tasks
- **Forgetting & Archiving**: Manage memory lifecycle for relevance and efficiency

### 3.2 Universal Memory Container

Every piece of information in DevSynth's memory system is represented as a Memetic Unit, regardless of its original format or source:

```text
┌─────────────────────────────────────────────────────────────────┐
│                    Memetic Unit Container                       │
├─────────────────────────────────────────────────────────────────┤
│ Identity & Provenance    │ Cognitive Type   │ Semantic Descriptors │
│ • unit_id                │ • WORKING        │ • content_hash       │
│ • parent_id              │ • EPISODIC       │ • semantic_vector    │
│ • source                 │ • SEMANTIC       │ • keywords           │
│ • timestamps             │ • PROCEDURAL     │ • topic              │
├─────────────────────────────────────────────────────────────────┤
│ State & Governance       │ Relational Links │ Payload             │
│ • status                 │ • Explicit links │ • Any data type     │
│ • confidence_score       │ • Relationships  │ • Text, code, etc.  │
│ • salience_score         │ • Dependencies   │ • Structured data   │
│ • access_control         │                  │ • Binary data       │
│ • lifespan_policy        │                  │                     │
└─────────────────────────────────────────────────────────────────┘
```

## 4. Memetic Unit Schema

### 4.1 Core Data Structure

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

class MemeticSource(Enum):
    """Source types for memetic units."""
    USER_INPUT = "user_input"
    AGENT_SELF = "agent_self"
    LLM_RESPONSE = "llm_response"
    CODE_EXECUTION = "code_execution"
    TEST_RESULT = "test_result"
    FILE_INGESTION = "file_ingestion"
    API_RESPONSE = "api_response"
    ERROR_LOG = "error_log"
    METRIC_DATA = "metric_data"
    CONFIGURATION = "configuration"
    DOCUMENTATION = "documentation"

class CognitiveType(Enum):
    """Cognitive function types for memory processing."""
    WORKING = "working"      # Active manipulation, current context
    EPISODIC = "episodic"    # Experience record, chronological
    SEMANTIC = "semantic"    # General knowledge, world model
    PROCEDURAL = "procedural" # Skills, plans, executable knowledge

class MemeticStatus(Enum):
    """Lifecycle status of memetic units."""
    RAW = "raw"              # Initial ingestion, unprocessed
    PROCESSED = "processed"  # Basic processing complete
    CONSOLIDATED = "consolidated" # Pattern extracted, abstracted
    ARCHIVED = "archived"    # Low relevance, compressed
    DEPRECATED = "deprecated" # Outdated, marked for removal

@dataclass
class MemeticLink:
    """Represents a relationship between memetic units."""
    target_id: UUID
    relationship_type: str
    strength: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MemeticMetadata:
    """Comprehensive metadata for memetic units."""

    # Identity & Provenance
    unit_id: UUID = field(default_factory=uuid4)
    parent_id: Optional[UUID] = None  # Causal predecessor
    source: MemeticSource = MemeticSource.USER_INPUT
    timestamp_created: datetime = field(default_factory=datetime.now)
    timestamp_accessed: Optional[datetime] = None
    timestamp_modified: Optional[datetime] = None

    # Cognitive Type
    cognitive_type: CognitiveType = CognitiveType.WORKING

    # Semantic Descriptors
    content_hash: str = ""
    semantic_vector: List[float] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    topic: str = ""
    summary: str = ""

    # State & Governance
    status: MemeticStatus = MemeticStatus.RAW
    confidence_score: float = 1.0
    salience_score: float = 0.5
    access_count: int = 0
    access_control: Dict[str, Any] = field(default_factory=dict)
    lifespan_policy: Dict[str, Any] = field(default_factory=dict)

    # Relational Links
    links: List[MemeticLink] = field(default_factory=list)

    # Quality Metrics
    validation_score: float = 0.0
    consistency_score: float = 0.0
    relevance_score: float = 0.0

@dataclass
class MemeticUnit:
    """Universal container for all memory types with rich metadata."""

    # Core Components
    metadata: MemeticMetadata
    payload: Any  # Modality-agnostic content

    def __post_init__(self):
        """Initialize derived fields and validate structure."""
        if not self.metadata.unit_id:
            self.metadata.unit_id = uuid4()

        if not self.metadata.timestamp_created:
            self.metadata.timestamp_created = datetime.now()

        # Generate content hash if not provided
        if not self.metadata.content_hash and self.payload:
            self.metadata.content_hash = self._generate_content_hash()

        # Update access timestamp
        self.metadata.timestamp_accessed = datetime.now()
        self.metadata.access_count += 1

    def _generate_content_hash(self) -> str:
        """Generate hash of payload content for deduplication."""
        import hashlib
        import json

        # Normalize payload for consistent hashing
        if isinstance(self.payload, (dict, list)):
            normalized = json.dumps(self.payload, sort_keys=True)
        elif isinstance(self.payload, str):
            normalized = self.payload
        else:
            normalized = str(self.payload)

        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def add_link(self, target_id: UUID, relationship_type: str, strength: float = 1.0, **metadata):
        """Add a relationship to another memetic unit."""
        link = MemeticLink(
            target_id=target_id,
            relationship_type=relationship_type,
            strength=strength,
            metadata=metadata
        )
        self.metadata.links.append(link)

    def update_salience(self, context: Dict[str, Any]) -> None:
        """Update salience score based on context and usage patterns."""
        base_salience = self.metadata.salience_score

        # Boost salience for recent access
        time_factor = self._calculate_time_factor()

        # Boost salience for relevant context
        context_factor = self._calculate_context_factor(context)

        # Boost salience for high confidence
        confidence_factor = self.metadata.confidence_score

        # Calculate new salience
        new_salience = (base_salience * 0.6 +
                       time_factor * 0.2 +
                       context_factor * 0.15 +
                       confidence_factor * 0.05)

        self.metadata.salience_score = min(1.0, max(0.0, new_salience))

    def _calculate_time_factor(self) -> float:
        """Calculate time-based salience factor."""
        if not self.metadata.timestamp_accessed:
            return 0.0

        hours_since_access = (datetime.now() - self.metadata.timestamp_accessed).total_seconds() / 3600

        # Exponential decay with half-life of 24 hours
        import math
        return math.exp(-hours_since_access / 24.0)

    def _calculate_context_factor(self, context: Dict[str, Any]) -> float:
        """Calculate context relevance factor."""
        if not context or not self.metadata.keywords:
            return 0.5

        # Check keyword overlap with context
        context_keywords = set()
        for value in context.values():
            if isinstance(value, str):
                context_keywords.update(value.lower().split())

        unit_keywords = set(word.lower() for word in self.metadata.keywords)

        if not context_keywords or not unit_keywords:
            return 0.5

        overlap = len(context_keywords.intersection(unit_keywords))
        return overlap / len(unit_keywords) if unit_keywords else 0.5

    def is_expired(self) -> bool:
        """Check if unit has exceeded its lifespan policy."""
        if not self.metadata.lifespan_policy:
            return False

        policy = self.metadata.lifespan_policy

        # Check time-based expiration
        if "max_age_hours" in policy:
            max_age = policy["max_age_hours"]
            age_hours = (datetime.now() - self.metadata.timestamp_created).total_seconds() / 3600
            if age_hours > max_age:
                return True

        # Check access-based expiration
        if "max_inactive_hours" in policy:
            if self.metadata.timestamp_accessed:
                inactive_hours = (datetime.now() - self.metadata.timestamp_accessed).total_seconds() / 3600
                if inactive_hours > policy["max_inactive_hours"]:
                    return True

        return False

    def get_age_hours(self) -> float:
        """Get age of unit in hours."""
        return (datetime.now() - self.metadata.timestamp_created).total_seconds() / 3600

    def get_inactive_hours(self) -> float:
        """Get time since last access in hours."""
        if not self.metadata.timestamp_accessed:
            return self.get_age_hours()
        return (datetime.now() - self.metadata.timestamp_accessed).total_seconds() / 3600
```

### 4.2 Metadata Schema Categories

| Category | Fields | Purpose | Validation Rules |
|----------|--------|---------|------------------|
| **Identity & Provenance** | `unit_id`, `parent_id`, `source`, `timestamp_*` | Trace origin and causal chains | UUID uniqueness, temporal ordering |
| **Cognitive Type** | `cognitive_type` | Determine storage and processing rules | Must be valid CognitiveType enum |
| **Semantic Descriptors** | `content_hash`, `semantic_vector`, `keywords`, `topic` | Enable intelligent retrieval | Hash consistency, vector normalization |
| **State & Governance** | `status`, `confidence_score`, `salience_score`, `access_control`, `lifespan_policy` | Manage lifecycle and quality | Score bounds (0-1), policy validation |
| **Relational Links** | `links` | Support graph-based reasoning | Link integrity, bidirectional consistency |

## 5. Memetic Unit Processing Pipeline

### 5.1 Ingestion Pipeline

Transform raw data into structured Memetic Units:

```python
class MemeticUnitIngestionPipeline:
    """Pipeline for transforming raw data into Memetic Units."""

    def process_raw_input(self, raw_data: Any, source: MemeticSource, context: Dict[str, Any] = None) -> MemeticUnit:
        """Convert raw input into a properly annotated Memetic Unit."""
        # Generate unique ID and timestamps
        unit_id = uuid4()
        timestamp = datetime.now()

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

        return unit

    def _classify_cognitive_type(self, data: Any, source: MemeticSource, context: Dict) -> CognitiveType:
        """Classify data into appropriate cognitive type."""
        # Agent interactions and current tasks -> WORKING
        if source in [MemeticSource.AGENT_SELF, MemeticSource.LLM_RESPONSE]:
            return CognitiveType.WORKING

        # Historical records and experiences -> EPISODIC
        if source in [MemeticSource.CODE_EXECUTION, MemeticSource.TEST_RESULT, MemeticSource.ERROR_LOG]:
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
        # For now, return placeholder vector
        import hashlib
        hash_obj = hashlib.md5(str(data).encode())
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

    def _extract_keywords(self, data: Any) -> List[str]:
        """Extract meaningful keywords from content."""
        import re

        text = str(data).lower()

        # Remove code-like patterns and extract words
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.split()

        # Filter for meaningful words (length > 2, not common stop words)
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        meaningful_words = [
            word for word in words
            if len(word) > 2 and word not in stop_words
        ]

        # Return top keywords (simplified)
        return meaningful_words[:10] if meaningful_words else ["general"]

    def _classify_topic(self, data: Any, keywords: List[str]) -> str:
        """Classify content into high-level topic categories."""
        text = str(data).lower()

        # Topic classification rules
        if any(word in text for word in ['error', 'exception', 'fail', 'bug']):
            return 'error_handling'
        elif any(word in text for word in ['test', 'assert', 'verify', 'validate']):
            return 'testing'
        elif any(word in text for word in ['function', 'class', 'method', 'code']):
            return 'code_structure'
        elif any(word in text for word in ['require', 'spec', 'design', 'plan']):
            return 'requirements'
        elif any(word in text for word in ['user', 'interface', 'ui', 'experience']):
            return 'user_experience'
        else:
            return 'general'
```

### 5.2 Memory Layer Integration

Integrate Memetic Units with existing memory layers:

```python
class MemeticUnitLayerIntegration:
    """Integration of Memetic Units with CTM memory layers."""

    def route_to_appropriate_layer(self, unit: MemeticUnit) -> str:
        """Route unit to appropriate memory layer based on cognitive type."""
        layer_mapping = {
            CognitiveType.WORKING: "working_memory",
            CognitiveType.EPISODIC: "episodic_buffer",
            CognitiveType.SEMANTIC: "semantic_store",
            CognitiveType.PROCEDURAL: "procedural_archive"
        }

        return layer_mapping.get(unit.metadata.cognitive_type, "working_memory")

    def enhance_memory_adapters(self, memory_manager) -> None:
        """Enhance existing memory adapters to use Memetic Units."""
        # Wrap vector store adapter
        if hasattr(memory_manager, 'vector_store'):
            memory_manager.vector_store = MemeticUnitVectorAdapter(
                memory_manager.vector_store
            )

        # Wrap graph store adapter
        if hasattr(memory_manager, 'graph_store'):
            memory_manager.graph_store = MemeticUnitGraphAdapter(
                memory_manager.graph_store
            )

        # Wrap document store adapter
        if hasattr(memory_manager, 'document_store'):
            memory_manager.document_store = MemeticUnitDocumentAdapter(
                memory_manager.document_store
            )

    def migrate_existing_data(self, memory_manager) -> int:
        """Migrate existing memory data to Memetic Unit format."""
        migrated_count = 0

        # Migrate vector store data
        if hasattr(memory_manager, 'vector_store'):
            migrated_count += self._migrate_vector_data(memory_manager.vector_store)

        # Migrate graph store data
        if hasattr(memory_manager, 'graph_store'):
            migrated_count += self._migrate_graph_data(memory_manager.graph_store)

        # Migrate document store data
        if hasattr(memory_manager, 'document_store'):
            migrated_count += self._migrate_document_data(memory_manager.document_store)

        return migrated_count

    def _migrate_vector_data(self, vector_store) -> int:
        """Migrate existing vector data to Memetic Units."""
        # This would iterate through existing vector data and wrap it in Memetic Units
        # Implementation depends on specific vector store interface
        pass
```

## 6. Integration with DevSynth Components

### 6.1 EDRR Integration

Memetic Units enhance each EDRR phase:

```python
class MemeticUnitEDRRIntegration:
    """Integration of Memetic Units with EDRR framework."""

    def enhance_expand_phase(self, query: str, memory_manager) -> List[MemeticUnit]:
        """Enhance expand phase with Memetic Unit retrieval."""
        # Query across all cognitive types for diverse examples
        working_context = memory_manager.get_units_by_type(CognitiveType.WORKING)
        semantic_patterns = memory_manager.get_units_by_type(CognitiveType.SEMANTIC)
        procedural_examples = memory_manager.get_units_by_type(CognitiveType.PROCEDURAL)

        return working_context + semantic_patterns + procedural_examples

    def enhance_differentiate_phase(self, alternatives: List[Solution]) -> ComparisonResult:
        """Enhance differentiate phase with Memetic Unit analysis."""
        # Compare alternatives using semantic similarity
        semantic_comparisons = self._compare_semantic_similarity(alternatives)

        # Analyze historical outcomes
        historical_analysis = self._analyze_historical_outcomes(alternatives)

        # Assess confidence and reliability
        confidence_analysis = self._assess_solution_confidence(alternatives)

        return ComparisonResult(
            semantic_comparisons=semantic_comparisons,
            historical_analysis=historical_analysis,
            confidence_analysis=confidence_analysis
        )

    def enhance_refine_phase(self, solution: Solution) -> RefinedSolution:
        """Enhance refine phase with procedural memory."""
        # Find similar successful refinements
        similar_refinements = self._find_similar_refinements(solution)

        # Extract procedural patterns
        procedural_patterns = self._extract_procedural_patterns(similar_refinements)

        # Apply learned improvements
        refined_solution = self._apply_procedural_improvements(solution, procedural_patterns)

        return refined_solution

    def enhance_retrospect_phase(self, outcome: Outcome) -> List[Insight]:
        """Enhance retrospect phase with episodic consolidation."""
        # Create episodic unit for current experience
        episodic_unit = MemeticUnit(
            metadata=MemeticMetadata(
                cognitive_type=CognitiveType.EPISODIC,
                source=MemeticSource.AGENT_SELF,
                status=MemeticStatus.RAW
            ),
            payload=outcome.to_dict()
        )

        # Extract patterns and lessons
        insights = self._extract_insights_from_outcome(outcome)

        # Create semantic units for learned patterns
        semantic_units = []
        for insight in insights:
            semantic_unit = MemeticUnit(
                metadata=MemeticMetadata(
                    cognitive_type=CognitiveType.SEMANTIC,
                    source=MemeticSource.AGENT_SELF,
                    status=MemeticStatus.CONSOLIDATED,
                    confidence_score=insight.confidence
                ),
                payload=insight.description
            )
            semantic_units.append(semantic_unit)

        return [episodic_unit] + semantic_units
```

### 6.2 Agent System Integration

Memetic Units provide rich context for agent reasoning:

```python
class MemeticUnitAgentEnhancement:
    """Enhance agents with Memetic Unit capabilities."""

    def enhance_agent_memory(self, agent, memory_manager) -> None:
        """Add Memetic Unit support to agent."""
        # Provide agent with Memetic Unit creation capabilities
        agent.create_memetic_unit = self._create_memetic_unit_function(memory_manager)

        # Provide agent with enhanced retrieval capabilities
        agent.retrieve_enhanced_context = self._create_enhanced_retrieval_function(memory_manager)

        # Provide agent with memory consolidation capabilities
        agent.consolidate_memories = self._create_consolidation_function(memory_manager)

    def _create_memetic_unit_function(self, memory_manager):
        """Create function for agents to create Memetic Units."""
        def create_unit(data: Any, cognitive_type: CognitiveType, source: MemeticSource = None) -> MemeticUnit:
            if source is None:
                source = MemeticSource.AGENT_SELF

            unit = memory_manager.ingestion_pipeline.process_raw_input(
                raw_data=data,
                source=source,
                context={"agent_context": True}
            )

            # Set cognitive type
            unit.metadata.cognitive_type = cognitive_type

            # Store in appropriate layer
            layer_name = memory_manager.route_to_layer(unit)
            memory_manager.store_in_layer(unit, layer_name)

            return unit

        return create_unit

    def _create_enhanced_retrieval_function(self, memory_manager):
        """Create function for agents to retrieve enhanced context."""
        def retrieve_context(query: str, cognitive_types: List[CognitiveType] = None) -> List[MemeticUnit]:
            if cognitive_types is None:
                cognitive_types = [CognitiveType.WORKING, CognitiveType.SEMANTIC]

            # Query across specified cognitive types
            relevant_units = []
            for cog_type in cognitive_types:
                layer_units = memory_manager.get_units_by_type(cog_type, query)
                relevant_units.extend(layer_units)

            # Sort by relevance and recency
            relevant_units.sort(key=lambda u: (u.metadata.salience_score, -u.get_age_hours()))

            return relevant_units[:10]  # Return top 10 most relevant

        return retrieve_context
```

## 7. Implementation Details

### 7.1 Storage Backend Integration

Integrate Memetic Units with existing memory backends:

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
        # Create node with unit properties
        node = GraphNode(
            id=str(unit.metadata.unit_id),
            type=unit.metadata.cognitive_type.value,
            properties={
                "source": unit.metadata.source.value,
                "status": unit.metadata.status.value,
                "confidence_score": unit.metadata.confidence_score,
                "salience_score": unit.metadata.salience_score,
                "content_hash": unit.metadata.content_hash,
                "summary": unit.metadata.summary
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

    def adapt_from_storage(self, stored_data: Any, data_type: str) -> MemeticUnit:
        """Reconstruct Memetic Unit from stored data."""
        if data_type == "vector":
            return self._reconstruct_from_vector_data(stored_data)
        elif data_type == "graph":
            return self._reconstruct_from_graph_data(stored_data)
        elif data_type == "document":
            return self._reconstruct_from_document_data(stored_data)
        else:
            raise ValueError(f"Unknown data type: {data_type}")

    def _reconstruct_from_vector_data(self, vector_doc: VectorDocument) -> MemeticUnit:
        """Reconstruct Memetic Unit from vector document."""
        # Parse metadata back into MemeticMetadata
        metadata = MemeticMetadata(
            unit_id=UUID(vector_doc.id),
            source=MemeticSource(vector_doc.metadata["source"]),
            cognitive_type=CognitiveType(vector_doc.metadata["cognitive_type"]),
            status=MemeticStatus(vector_doc.metadata["status"]),
            confidence_score=vector_doc.metadata["confidence_score"],
            salience_score=vector_doc.metadata["salience_score"],
            timestamp_created=datetime.fromisoformat(vector_doc.metadata["timestamp_created"]),
            keywords=vector_doc.metadata.get("keywords", []),
            topic=vector_doc.metadata.get("topic", ""),
            content_hash=vector_doc.metadata["content_hash"]
        )

        return MemeticUnit(metadata=metadata, payload=vector_doc.content)
```

### 7.2 Performance Optimization

Optimize Memetic Unit operations for production use:

```python
class MemeticUnitPerformanceOptimizer:
    """Performance optimization for Memetic Unit operations."""

    def optimize_memory_operations(self, memory_manager) -> OptimizedMemoryManager:
        """Optimize memory operations for Memetic Unit usage."""
        # Add caching layer for metadata
        metadata_cache = self._create_metadata_cache()

        # Optimize vector operations
        vector_optimization = self._optimize_vector_operations()

        # Optimize graph traversals
        graph_optimization = self._optimize_graph_traversals()

        return OptimizedMemoryManager(
            base_manager=memory_manager,
            metadata_cache=metadata_cache,
            vector_optimization=vector_optimization,
            graph_optimization=graph_optimization
        )

    def _create_metadata_cache(self) -> MetadataCache:
        """Create efficient cache for metadata operations."""
        # Use LRU cache for frequently accessed metadata
        cache = LRUCache(max_size=1000, ttl_seconds=3600)

        # Cache strategies:
        # 1. Cache unit lookups by ID
        # 2. Cache semantic similarity computations
        # 3. Cache topic classifications
        # 4. Cache salience calculations

        return cache

    def _optimize_vector_operations(self) -> VectorOptimization:
        """Optimize vector operations for Memetic Units."""
        return VectorOptimization(
            batch_size=32,
            similarity_threshold=0.7,
            max_results=100,
            use_approximate_search=True
        )

    def _optimize_graph_traversals(self) -> GraphOptimization:
        """Optimize graph traversals for Memetic Unit relationships."""
        return GraphOptimization(
            max_traversal_depth=5,
            relationship_cache_size=5000,
            use_path_indexing=True,
            enable_parallel_traversal=True
        )
```

## 8. Configuration

### 8.1 Memetic Unit Configuration Schema

```yaml
memetic_units:
  enabled: true

  ingestion:
    auto_classify_cognitive_type: true
    generate_semantic_vectors: true
    extract_keywords: true
    classify_topics: true
    compute_confidence_scores: true

  governance:
    default_lifespan_hours: 720  # 30 days
    max_inactive_hours: 168     # 7 days
    confidence_threshold: 0.6
    salience_decay_rate: 0.95

  performance:
    cache_enabled: true
    cache_size: 1000
    cache_ttl_seconds: 3600
    batch_processing_size: 32
    parallel_processing: true

  integration:
    memory_manager_enabled: true
    agent_system_enabled: true
    edrr_enabled: true
    existing_data_migration: true
    backward_compatibility: true

  quality:
    validation_enabled: true
    consistency_checking: true
    deduplication_enabled: true
    metadata_integrity: true
```

## 9. Testing Strategy

### 9.1 Unit Testing

```gherkin
Feature: Memetic Unit Abstraction
  As a DevSynth developer
  I want a universal memory representation with rich metadata
  So that all information can be consistently processed and retrieved

  Background:
    Given the Memetic Unit system is configured and initialized
    And metadata validation is enabled
    And cognitive type classification is active

  @memetic_unit_creation @metadata_schema @high_priority
  Scenario: Create Memetic Unit with comprehensive metadata
    Given I have raw data from various sources
    When I process the data through the ingestion pipeline
    Then a valid Memetic Unit should be created
    And all metadata fields should be populated correctly
    And the cognitive type should be classified appropriately
    And semantic descriptors should be generated
    And the content hash should be computed
    And governance fields should be initialized

  @cognitive_type_classification @source_routing @medium_priority
  Scenario: Classify data into appropriate cognitive types
    Given I have data from different sources
    When the system classifies the cognitive type
    Then user input should be classified as WORKING memory
    And code execution results should be classified as EPISODIC memory
    And documentation should be classified as SEMANTIC memory
    And API responses should be classified as PROCEDURAL memory
    And classification should be deterministic and consistent

  @metadata_governance @lifecycle_management @medium_priority
  Scenario: Manage Memetic Unit lifecycle and governance
    Given I have Memetic Units with different ages and access patterns
    When the governance system processes the units
    Then salience scores should be updated based on usage
    And confidence scores should reflect data quality
    And expired units should be identified correctly
    And access patterns should influence retention decisions
    And governance should not affect unit functionality
```

## 10. Migration Strategy

### 10.1 Backward Compatibility

- Existing memory operations continue to work unchanged
- Memetic Unit features are opt-in via configuration
- Gradual migration path for existing memory stores

### 10.2 Data Migration

1. **Phase 1**: Analyze existing memory data structure and content
2. **Phase 2**: Create Memetic Unit wrappers for existing data
3. **Phase 3**: Migrate metadata and enhance with semantic descriptors
4. **Phase 4**: Validate migrated data maintains all functionality
5. **Phase 5**: Enable enhanced features for new data

## 11. Requirements

- **MEM-001**: Memetic Units must support all metadata categories (identity, cognitive, semantic, governance, relational)
- **MEM-002**: Cognitive type classification must achieve >95% accuracy for known data patterns
- **MEM-003**: Content deduplication must identify identical content with >99% accuracy
- **MEM-004**: Memory governance must maintain system performance while managing lifecycle
- **MEM-005**: Integration must maintain backward compatibility with existing memory operations

## Implementation Status

This specification defines the **planned** Memetic Unit abstraction. Implementation will proceed in phases as outlined in the migration strategy.

## References

- [Cognitive-Temporal Memory Framework Specification](cognitive_temporal_memory_framework.md)
- [Enhanced Knowledge Graph with Business Intent Layer](enhanced_knowledge_graph_intent_layer.md)
- [Hybrid Memory Architecture Specification](hybrid_memory_architecture.md)
- [From Code to Context - Holistic Paradigms for LLM Software Comprehension](../../inspirational_docs/From Code to Context_ A Critical Evaluation of Holistic Paradigms for LLM Software Comprehension.md)

## What proofs confirm the solution?

- BDD scenarios in [`tests/behavior/features/memetic_unit_abstraction.feature`](../../tests/behavior/features/memetic_unit_abstraction.feature) ensure termination and expected outcomes.
- Finite state transitions in metadata processing guarantee termination.
- Empirical validation through metadata completeness and cognitive type classification accuracy metrics.
- Performance benchmarks ensuring <10% overhead for metadata operations while providing comprehensive memory management capabilities.
