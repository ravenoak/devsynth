---
title: "Cognitive-Temporal Memory (CTM) Framework Specification"
date: "2025-07-10"
version: "0.1.0a1"
tags:
  - "specification"
  - "memory"
  - "cognitive-architecture"
  - "agentic-ai"

status: "published"
author: "DevSynth Team"
last_reviewed: "2025-07-10"
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Specifications</a> &gt; Cognitive-Temporal Memory Framework Specification
</div>

# Cognitive-Temporal Memory (CTM) Framework Specification

## 1. Overview

The Cognitive-Temporal Memory (CTM) Framework implements a multi-layered, functionally-differentiated memory architecture inspired by human cognitive science. This specification defines the CTM paradigm for DevSynth, providing a robust foundation for advanced agentic AI capabilities.

## 2. Purpose and Goals

The CTM Framework aims to:

1. **Elevate Memory to First-Class Status**: Treat memory as a core operational resource with managed lifecycle
2. **Implement Functional Differentiation**: Structure memory by cognitive function rather than temporal duration
3. **Enable Temporal Reasoning**: Support reasoning about time, causality, and experience sequences
4. **Provide Automated Context Engineering**: Automate the assembly of optimal context for LLM reasoning
5. **Support Advanced Agent Capabilities**: Enable sophisticated planning, learning, and adaptation
6. **Scale with Project Complexity**: Maintain performance across varying project sizes and complexities

## 3. Core Philosophy

### 3.1 Memory as a Managed Resource

The CTM paradigm treats memory as a comprehensive operating system analogous to MemOS, actively governing the entire information lifecycle:

- **Ingestion & Annotation**: Transform raw data into structured, traceable Memetic Units
- **Consolidation & Abstraction**: Extract patterns and create higher-level knowledge
- **Retrieval & Context Assembly**: Provide optimal context for reasoning tasks
- **Forgetting & Archiving**: Manage memory lifecycle for relevance and efficiency

### 3.2 Multi-Layered Functional Structure

The architecture explicitly differentiates between four cognitive functions:

```text
┌─────────────────────────────────────────────────────────────┐
│                    Cognitive Functions                       │
├─────────────────────────────────────────────────────────────┤
│ Working Memory      │ Active manipulation of current context    │
│ Episodic Memory     │ Autobiographical record of experiences    │
│ Semantic Memory     │ General knowledge and world model        │
│ Procedural Memory   │ Skills, plans, and executable knowledge  │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Temporal and Causal Organization

Every memory unit is timestamped and linked to its causal chain, enabling:

- **Temporal Queries**: Reason about sequences of events and their timing
- **Causal Tracing**: Understand cause-and-effect relationships between actions
- **Experience Learning**: Learn from historical patterns and outcomes

## 4. Memetic Unit Abstraction

### 4.1 Universal Memory Container

The Memetic Unit serves as a standardized container for all forms of memory:

```python
@dataclass
class MemeticUnit:
    """Universal container for all memory types with rich metadata."""

    # Identity & Provenance
    unit_id: UUID
    parent_id: Optional[UUID]  # Causal predecessor
    source: MemeticSource  # USER_INPUT, AGENT_SELF, TOOL_X, etc.
    timestamp_created: datetime
    timestamp_accessed: Optional[datetime]

    # Cognitive Type
    cognitive_type: CognitiveType  # WORKING, EPISODIC, SEMANTIC, PROCEDURAL

    # Semantic Descriptors
    content_hash: str
    semantic_vector: List[float]
    keywords: List[str]
    topic: str

    # State & Governance
    status: MemeticStatus  # RAW, PROCESSED, CONSOLIDATED, ARCHIVED, DEPRECATED
    confidence_score: float
    salience_score: float
    access_control: Dict[str, Any]
    lifespan_policy: Dict[str, Any]

    # Relational Links
    links: List[MemeticLink]  # Explicit relationships to other units

    # Payload (modality-agnostic)
    payload: Any  # Text, structured data, code, etc.
```

### 4.2 Metadata Schema Categories

| Category | Fields | Purpose |
|----------|--------|---------|
| **Identity & Provenance** | `unit_id`, `parent_id`, `source`, `timestamp_*` | Trace origin and causal chains |
| **Cognitive Type** | `cognitive_type` | Determine storage and processing rules |
| **Semantic Descriptors** | `content_hash`, `semantic_vector`, `keywords`, `topic` | Enable intelligent retrieval |
| **State & Governance** | `status`, `confidence_score`, `salience_score`, `access_control`, `lifespan_policy` | Manage lifecycle and quality |
| **Relational Links** | `links` | Support graph-based reasoning |

## 5. Four Functional Memory Layers

### 5.1 Layer 1: Working Memory (Cognitive Present)

**Function**: Active manipulation of current context for reasoning and decision-making.

**Implementation**:
- **Storage**: In-memory data structures (deque, list, graph)
- **Capacity**: Limited to LLM's effective context window
- **Operations**: Push, pop, manipulate, clear
- **Optimization**: Priority-based retention and context pruning

**Integration Points**:
- LLM prompt construction
- Chain-of-Thought reasoning
- Multi-step planning
- Context window management

### 5.2 Layer 2: Episodic Buffer (Stream of Experience)

**Function**: Immutable, chronological record of all agent experiences and interactions.

**Implementation**:
- **Storage**: Time-series database or append-only log
- **Properties**: Immutable, append-only, efficient temporal queries
- **Operations**: Write (append), query by time/source, pattern extraction

**Integration Points**:
- Conversation history
- Tool usage logs
- Error and success tracking
- Learning from experience

### 5.3 Layer 3: Semantic Store (Evolving World Model)

**Function**: Structured knowledge base of general facts, concepts, and their relationships.

**Implementation**:
- **Storage**: Hybrid graph + vector database
- **Graph Component**: Entities and typed relationships (Neo4j/NebulaGraph)
- **Vector Component**: Semantic embeddings for similarity search
- **Operations**: Query, update, consolidate, resolve conflicts

**Integration Points**:
- Project knowledge base
- Code and documentation relationships
- Requirements and specifications
- Cross-reference linking

### 5.4 Layer 4: Procedural Archive (Library of Skills)

**Function**: Repository of executable skills, plans, and capabilities.

**Implementation**:
- **Storage**: Function registry + plan library
- **Components**: Tool definitions, execution plans, learned procedures
- **Operations**: Query by capability, execute, register new skills

**Integration Points**:
- Tool and function definitions
- Workflow templates
- Best practice patterns
- Skill learning and adaptation

## 6. Memory Operating System (MemOS)

### 6.1 Core Processes

#### 6.1.1 Ingestion & Annotation Pipeline

Transform raw data into structured Memetic Units:

```python
class IngestionPipeline:
    """Pipeline for transforming raw data into Memetic Units."""

    def process_input(self, raw_data: Any, source: MemeticSource) -> MemeticUnit:
        """Convert raw input into a properly annotated Memetic Unit."""
        # Generate unique ID and timestamps
        unit_id = uuid.uuid4()
        timestamp = datetime.now()

        # Determine cognitive type based on content analysis
        cognitive_type = self._classify_cognitive_type(raw_data)

        # Generate semantic descriptors
        content_hash = self._compute_hash(raw_data)
        semantic_vector = self._generate_embedding(raw_data)
        keywords = self._extract_keywords(raw_data)
        topic = self._classify_topic(raw_data)

        # Create metadata
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
            confidence_score=1.0,
            salience_score=0.5
        )

        return MemeticUnit(payload=raw_data, metadata=metadata)
```

#### 6.1.2 Consolidation & Abstraction Process

Extract patterns and create higher-level knowledge:

```python
class ConsolidationProcess:
    """Process for abstracting episodic experiences into semantic knowledge."""

    def run_consolidation_cycle(self) -> List[MemeticUnit]:
        """Scan episodic buffer and create semantic/procedural abstractions."""
        # Query recent episodic memories
        recent_episodes = self._query_recent_episodes()

        # Identify patterns and repetitions
        patterns = self._identify_patterns(recent_episodes)

        # Create semantic units from patterns
        semantic_units = []
        for pattern in patterns:
            semantic_unit = self._create_semantic_unit(pattern)
            semantic_units.append(semantic_unit)

        # Create procedural units from successful sequences
        procedural_units = []
        for successful_sequence in self._find_successful_sequences(recent_episodes):
            procedural_unit = self._create_procedural_unit(successful_sequence)
            procedural_units.append(procedural_unit)

        return semantic_units + procedural_units
```

#### 6.1.3 Retrieval & Context Assembly

Automate optimal context provision:

```python
class ContextAssemblyEngine:
    """Engine for assembling optimal context across memory layers."""

    def assemble_context(self, task: Task) -> ContextAssembly:
        """Assemble optimal context for the given task."""
        # Analyze task requirements
        task_analysis = self._analyze_task_requirements(task)

        # Query each memory layer based on task needs
        working_context = self._query_working_memory(task_analysis)
        episodic_context = self._query_episodic_memory(task_analysis)
        semantic_context = self._query_semantic_memory(task_analysis)
        procedural_context = self._query_procedural_memory(task_analysis)

        # Assemble and optimize context
        assembly = ContextAssembly(
            task=task,
            working_memory=working_context,
            episodic_context=episodic_context,
            semantic_context=semantic_context,
            procedural_context=procedural_context
        )

        return self._optimize_assembly(assembly)
```

#### 6.1.4 Forgetting & Archiving Process

Manage memory lifecycle and relevance:

```python
class MemoryGovernance:
    """Process for managing memory lifecycle and relevance."""

    def apply_forgetting_policies(self) -> int:
        """Apply forgetting policies and return number of units forgotten."""
        # Calculate salience scores for all units
        self._update_salience_scores()

        # Apply time-based decay
        self._apply_time_decay()

        # Apply access-frequency decay
        self._apply_access_decay()

        # Archive low-salience units
        archived_count = self._archive_low_salience_units()

        # Remove deprecated units
        removed_count = self._remove_deprecated_units()

        return archived_count + removed_count
```

## 7. Integration with DevSynth Components

### 7.1 EDRR Integration

The CTM framework enhances each EDRR phase:

| EDRR Phase | CTM Enhancement | Memory Layer Focus |
|------------|-----------------|-------------------|
| **Expand** | Vector similarity for diverse examples | Semantic + Procedural |
| **Differentiate** | Graph traversal for relationship analysis | Semantic (Graph) |
| **Refine** | Historical pattern matching | Episodic + Semantic |
| **Retrospect** | Learning from experience | Episodic → Semantic |

### 7.2 WSDE Model Integration

CTM supports WSDE agent roles:

| WSDE Role | CTM Memory Access | Specialized Capabilities |
|-----------|------------------|------------------------|
| **Primus** | All memory layers | Coordination and synthesis |
| **Worker** | Focused context + tools | Task execution and results |
| **Supervisor** | Quality metrics + standards | Validation and critique |
| **Designer** | Architectural patterns | Design reasoning and planning |
| **Evaluator** | Requirements + criteria | Assessment and feedback |

### 7.3 Memory Manager Integration

The existing MemoryManager is enhanced to support CTM:

```python
class CTMMemoryManager(MemoryManager):
    """CTM-enhanced memory manager with cognitive layers."""

    def __init__(self, config: CTMConfig):
        super().__init__(config)
        self.ctm_layers = self._initialize_ctm_layers()
        self.mem_os = MemoryOperatingSystem(self.ctm_layers)

    def store_cognitively(self, data: Any, cognitive_type: CognitiveType) -> MemeticUnit:
        """Store data with cognitive type awareness."""
        return self.mem_os.ingest(data, cognitive_type)

    def retrieve_cognitively(self, query: Any, task_context: TaskContext) -> ContextAssembly:
        """Retrieve context with cognitive awareness."""
        return self.mem_os.assemble_context(query, task_context)
```

## 8. Implementation Roadmap

### 8.1 Phase 1: Foundation (Weeks 1-2)

**Deliverables:**
1. Memetic Unit implementation with full metadata schema
2. Basic four-layer architecture (in-memory implementations)
3. Core MemOS processes (ingestion, basic consolidation)
4. Integration with existing MemoryManager

**Success Criteria:**
- Memetic Units can be created and stored
- Basic retrieval works across all layers
- Existing functionality continues to work
- Performance impact < 10%

### 8.2 Phase 2: Cognitive Enhancement (Weeks 3-4)

**Deliverables:**
1. Advanced consolidation algorithms
2. Context assembly engine with task awareness
3. Memory governance and forgetting policies
4. Integration with EDRR reasoning loops

**Success Criteria:**
- Consolidation creates meaningful semantic units
- Context assembly improves LLM response quality
- Memory governance maintains relevance
- EDRR phases leverage appropriate memory layers

### 8.3 Phase 3: Production Readiness (Weeks 5-6)

**Deliverables:**
1. Persistent storage backends for all layers
2. Performance optimization and caching
3. Monitoring and diagnostics
4. Migration from existing memory system

**Success Criteria:**
- All memory layers use production-grade backends
- Performance meets or exceeds current system
- Comprehensive monitoring and debugging
- Zero-downtime migration possible

## 9. Configuration

### 9.1 CTM Configuration Schema

```yaml
ctm:
  enabled: true

  layers:
    working_memory:
      max_units: 100
      pruning_strategy: "relevance"  # relevance, fifo, lru
      persistence_enabled: true

    episodic_buffer:
      retention_days: 30
      compression_enabled: true
      batch_size: 1000

    semantic_store:
      graph_backend: "neo4j"  # neo4j, networkx, rdflib
      vector_backend: "chroma"  # chroma, faiss, qdrant
      consolidation_interval_minutes: 60

    procedural_archive:
      max_plans: 1000
      learning_enabled: true
      skill_extraction_threshold: 0.8

  mem_os:
    consolidation_interval_seconds: 300
    forgetting_interval_seconds: 3600
    context_assembly_timeout_seconds: 30

  integration:
    edrr_enabled: true
    wsde_enabled: true
    existing_memory_migration: true
```

## 10. Testing Strategy

### 10.1 Unit Testing

- Test each memory layer independently
- Verify Memetic Unit creation and metadata
- Test core MemOS processes in isolation
- Mock external dependencies

### 10.2 Integration Testing

- Test cross-layer interactions
- Verify EDRR and WSDE integrations
- Test memory persistence and recovery
- Performance testing for large-scale operations

### 10.3 Behavior Testing

- Test realistic agent workflows
- Verify learning and adaptation capabilities
- Test forgetting and relevance mechanisms
- Validate context assembly quality

## 11. Migration Strategy

### 11.1 Backward Compatibility

- Existing MemoryManager interface preserved
- Gradual migration of existing data
- Feature flags for CTM capabilities

### 11.2 Data Migration

1. **Phase 1**: Analyze existing memory stores
2. **Phase 2**: Map existing data to Memetic Units
3. **Phase 3**: Migrate data to appropriate CTM layers
4. **Phase 4**: Validate migrated data integrity

## 12. Requirements

- **CTM-001**: Memory layers must support the four cognitive functions (Working, Episodic, Semantic, Procedural)
- **CTM-002**: Memetic Units must include all required metadata fields
- **CTM-003**: Context assembly must improve LLM response quality by at least 20%
- **CTM-004**: Memory governance must maintain system performance across time
- **CTM-005**: Integration must not break existing DevSynth functionality

## Implementation Status

This specification defines the **planned** CTM framework. Implementation will proceed in phases as outlined in the roadmap.

## References

- [LLM Memory System Redesign - CTM Paradigm](../../inspirational_docs/LLM Memory System Redesign.txt)
- [Hybrid Memory Architecture Specification](hybrid_memory_architecture.md)
- [EDRR Framework Integration](edrr_framework_integration_summary.md)

## What proofs confirm the solution?

- BDD scenarios in [`tests/behavior/features/cognitive_temporal_memory_framework.feature`](../../tests/behavior/features/cognitive_temporal_memory_framework.feature) ensure termination and expected outcomes.
- Finite state transitions and bounded loops guarantee termination.
- Empirical validation through A/B testing of context assembly improvements.
