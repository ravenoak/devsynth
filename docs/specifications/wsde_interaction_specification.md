---

title: "WSDE Multi-Agent Interaction Specification"
date: "2025-07-07"
version: "0.1.0-alpha.1"
tags:
  - "specification"

status: "published"
author: "DevSynth Team"
last_reviewed: "2025-07-10"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Specifications</a> &gt; WSDE Multi-Agent Interaction Specification
</div>

# WSDE Multi-Agent Interaction Specification

## 1. Overview

The WSDE (Worker Self-Directed Enterprise) model in DevSynth provides a framework for organizing and coordinating multiple AI agents in collaborative software development tasks. This specification defines the interaction patterns, role responsibilities, and coordination mechanisms for the WSDE multi-agent system.

## 2. Purpose and Goals

The WSDE multi-agent interaction system aims to:

1. Enable effective collaboration between specialized AI agents
2. Distribute cognitive tasks across multiple agents with different perspectives
3. Implement checks and balances through peer review and consensus
4. Support dynamic role assignment based on task requirements
5. Facilitate dialectical reasoning through structured agent interactions


## 3. WSDE Roles and Responsibilities

### 3.1 Primus

**Purpose**: Coordinate the overall workflow and ensure alignment with project goals.

**Responsibilities**:

- Task decomposition and assignment
- Progress monitoring and coordination
- Conflict resolution between agents
- Integration of work products
- Communication with human users


**Decision Authority**:

- Workflow sequencing
- Resource allocation
- Final integration decisions
- Human intervention requests


### 3.2 Worker

**Purpose**: Execute specific development tasks and implement solutions.

**Responsibilities**:

- Code implementation
- Test development
- Documentation writing
- Artifact generation
- Technical problem-solving


**Decision Authority**:

- Implementation details
- Technical approaches
- Local optimizations
- Task-specific adaptations


### 3.3 Supervisor

**Purpose**: Ensure quality and consistency across the development process.

**Responsibilities**:

- Quality assurance
- Standard enforcement
- Process oversight
- Risk identification
- Performance monitoring


**Decision Authority**:

- Quality acceptance
- Process adjustments
- Standard interpretations
- Risk mitigation strategies


### 3.4 Designer

**Purpose**: Create high-level designs and creative solutions.

**Responsibilities**:

- Architecture design
- Interface design
- Solution conceptualization
- Innovation exploration
- Pattern identification


**Decision Authority**:

- Design approaches
- Architectural decisions
- Creative directions
- Pattern applications


### 3.5 Evaluator

**Purpose**: Assess outputs and provide critical feedback.

**Responsibilities**:

- Output evaluation
- Dialectical critique
- Alternative perspective provision
- Improvement suggestion
- Validation against requirements


**Decision Authority**:

- Evaluation criteria
- Feedback prioritization
- Acceptance recommendations
- Improvement directions


## 4. Interaction Patterns

### 4.1 Consensus Decision Making

**Pattern**: Multiple agents collaborate to reach agreement on important decisions.

**Process**:

1. Issue identification by any agent
2. Proposal generation by assigned agent
3. Critique and counter-proposals by other agents
4. Synthesis of perspectives by Primus
5. Voting or weighted decision mechanism
6. Implementation of consensus decision


**Implementation**:

```python
class ConsensusDecision:
    def __init__(self, agents, decision_topic, decision_context):
        self.agents = agents
        self.topic = decision_topic
        self.context = decision_context
        self.proposals = []
        self.critiques = []
        self.votes = {}
        self.decision = None

    def collect_proposals(self):
        """Collect proposals from all agents."""
        pass

    def collect_critiques(self):
        """Collect critiques of each proposal."""
        pass

    def conduct_voting(self):
        """Conduct voting on proposals."""
        pass

    def synthesize_decision(self):
        """Synthesize final decision based on votes and critiques."""
        pass
```

### 4.2 Dialectical Reasoning

**Pattern**: Structured thesis-antithesis-synthesis process for problem-solving.

**Process**:

1. Thesis presentation by one agent
2. Antithesis development by another agent
3. Dialectical analysis by a third agent
4. Synthesis creation by Primus or Designer
5. Validation by Evaluator
6. Refinement based on feedback


**Implementation**:

```python
class DialecticalReasoning:
    def __init__(self, thesis_agent, antithesis_agent, synthesis_agent):
        self.thesis_agent = thesis_agent
        self.antithesis_agent = antithesis_agent
        self.synthesis_agent = synthesis_agent
        self.thesis = None
        self.antithesis = None
        self.synthesis = None

    def generate_thesis(self, problem_context):
        """Generate initial thesis."""
        pass

    def generate_antithesis(self):
        """Generate antithesis in response to thesis."""
        pass

    def generate_synthesis(self):
        """Generate synthesis from thesis and antithesis."""
        pass
```

### 4.3 Peer Review

**Pattern**: Systematic review of work products by peers.

**Process**:

1. Work submission by producing agent
2. Review assignment to one or more agents
3. Independent review execution
4. Feedback aggregation
5. Revision by original agent
6. Acceptance or further review


**Implementation**:

```python
class PeerReview:
    def __init__(self, work_product, author_agent, reviewer_agents):
        self.work_product = work_product
        self.author = author_agent
        self.reviewers = reviewer_agents
        self.reviews = {}
        self.revision = None
        self.status = "pending"

    def assign_reviews(self):
        """Assign review tasks to reviewers."""
        pass

    def collect_reviews(self):
        """Collect reviews from all reviewers."""
        pass

    def aggregate_feedback(self):
        """Aggregate feedback from all reviews."""
        pass

    def request_revision(self):
        """Request revision from author based on feedback."""
        pass
```

### 4.4 Role Rotation

**Pattern**: Dynamic reassignment of roles based on task needs and agent capabilities.

**Process**:

1. Task analysis by Primus
2. Capability matching with available agents
3. Role assignment proposal
4. Acceptance by assigned agents
5. Handover of responsibilities
6. Performance monitoring in new roles


**Implementation**:

```python
class RoleRotation:
    def __init__(self, agent_registry, task_context):
        self.agent_registry = agent_registry
        self.task_context = task_context
        self.current_assignments = {}
        self.proposed_assignments = {}

    def analyze_task_requirements(self):
        """Analyze task to determine role requirements."""
        pass

    def match_capabilities(self):
        """Match agent capabilities to role requirements."""
        pass

    def propose_assignments(self):
        """Propose new role assignments."""
        pass

    def execute_handover(self):
        """Execute handover of responsibilities."""
        pass
```

## 5. Coordination Mechanisms

### 5.1 Message Passing Protocol

**Purpose**: Enable structured communication between agents.

**Message Types**:

- **Task Assignment**: Delegation of work
- **Status Update**: Progress reporting
- **Information Request**: Knowledge seeking
- **Review Request**: Solicitation of feedback
- **Decision Request**: Request for decision input
- **Notification**: General information sharing


**Message Structure**:

```json
{
  "message_id": "unique-identifier",
  "message_type": "task_assignment",
  "sender": "agent-id",
  "recipients": ["agent-id-1", "agent-id-2"],
  "subject": "Brief description",
  "content": "Detailed message content",
  "metadata": {
    "priority": "high",
    "deadline": "ISO-timestamp",
    "context_references": ["ref-1", "ref-2"]
  },
  "timestamp": "ISO-timestamp"
}
```

### 5.2 Shared Memory Access

**Purpose**: Provide common knowledge repository for all agents.

**Access Patterns**:

- Read-only for reference information
- Read-write for collaborative artifacts
- Append-only for logs and history
- Transactional for critical updates


**Implementation**:

- Vector store for semantic search
- Graph store for relationship navigation
- Structured store for metadata and state
- Locking mechanisms for concurrent access


### 5.3 Workflow Orchestration

**Purpose**: Coordinate the sequence and dependencies of agent activities.

**Features**:

- Task dependency management
- Parallel task execution
- Synchronization points
- Exception handling
- Progress tracking
- Timeout management


**Implementation**:

- LangGraph-based workflow definitions
- Event-driven state transitions
- Persistent workflow state
- Human intervention hooks

### 5.4 Role Rotation and Consensus Workflow

**Purpose**: Distribute leadership while synthesizing group decisions.

**Workflow**:

1. Evaluate agents against task context and choose an unused expert as Primus.
2. Assign remaining roles to other agents in sequence.
3. Collect solutions from agents and synthesize a consensus from their contributions.
4. After each cycle, rotate the Primus role and reset usage flags when all agents have served.


## 6. Integration with Other Components

### 6.1 EDRR Integration

The WSDE multi-agent system integrates with the EDRR:

- **Expand**: Designer and Worker agents generate diverse approaches
- **Differentiate**: Evaluator and Supervisor agents analyze options
- **Refine**: Worker and Designer agents improve selected solutions
- **Retrospect**: All agents participate in review and learning


### 6.2 Memory System Integration

The WSDE multi-agent system leverages the hybrid memory system:

- Shared access to all memory stores
- Role-specific views and access patterns
- Agent communication history persistence
- Decision rationale documentation


### 6.3 Promise System Integration

The WSDE multi-agent system uses the Promise system for capability management:

- Role-specific capability requirements
- Capability verification for role assignment
- Authorization for sensitive operations
- Capability discovery for task matching


## 7. Implementation Details

### 7.1 Agent Registry

```python
class WSDETeam:
    """Manages a team of agents using the WSDE model."""

    def __init__(self, available_agents=None):
        self.available_agents = available_agents or []
        self.role_assignments = {
            "primus": None,
            "worker": [],
            "supervisor": None,
            "designer": None,
            "evaluator": None
        }

    def assign_roles(self, role_mapping=None):
        """Assign roles to agents based on mapping or automatically."""
        if role_mapping:
            # Validate and apply explicit mapping
            self._validate_role_mapping(role_mapping)
            self.role_assignments = role_mapping
        else:
            # Auto-assign based on agent capabilities
            self._auto_assign_roles()

        return self.role_assignments

    def get_agent_by_role(self, role):
        """Get agent(s) assigned to a specific role."""
        return self.role_assignments.get(role)

    def rotate_primus(self):
        """Rotate the Primus role among agents."""
        # Implementation details
        pass

    def _validate_role_mapping(self, mapping):
        """Validate that role mapping is valid."""
        # Implementation details
        pass

    def _auto_assign_roles(self):
        """Automatically assign roles based on agent capabilities."""
        # Implementation details
        pass
```

### 7.2 Interaction Manager

```python
class AgentInteractionManager:
    """Manages interactions between agents in the WSDE model."""

    def __init__(self, wsde_team, memory_manager):
        self.team = wsde_team
        self.memory_manager = memory_manager
        self.active_interactions = {}

    def initiate_consensus_decision(self, topic, context):
        """Initiate a consensus decision process."""
        # Implementation details
        pass

    def initiate_dialectical_reasoning(self, problem_context):
        """Initiate a dialectical reasoning process."""
        # Implementation details
        pass

    def initiate_peer_review(self, work_product, author_id):
        """Initiate a peer review process."""
        # Implementation details
        pass

    def initiate_role_rotation(self, task_context):
        """Initiate a role rotation process."""
        # Implementation details
        pass

    def send_message(self, sender_id, recipient_ids, message_type, subject, content, metadata=None):
        """Send a message between agents."""
        # Implementation details
        pass

    def get_messages(self, agent_id, filters=None):
        """Get messages for a specific agent."""
        # Implementation details
        pass
```

## 8. Configuration Options

The WSDE multi-agent interaction system can be customized through configuration:

- **Team Size**: Number of agents in the team
- **Role Distribution**: Allocation of agents to roles
- **Decision Thresholds**: Required consensus levels for different decisions
- **Review Policies**: Requirements for peer review processes
- **Communication Patterns**: Allowed message types and frequencies


## Current Limitations

The WSDE collaboration workflow now supports dynamic role rotation and consensus synthesis. These features are activated when the `features.wsde_collaboration` flag in `config/default.yml` is enabled. See the [Feature Status Matrix](../implementation/feature_status_matrix.md) for progress tracking.

## 9. Future Enhancements

Planned improvements to the WSDE multi-agent interaction system:

- **Specialized Agent Types**: Domain-specific agent specializations
- **Adaptive Team Composition**: Dynamic team sizing based on task complexity
- **Conflict Resolution Strategies**: Advanced mechanisms for resolving agent disagreements
- **Performance Analytics**: Metrics for team effectiveness and collaboration quality
- **Learning from Interactions**: Improvement of interaction patterns based on past performance


## 10. Conclusion

The WSDE multi-agent interaction specification provides a comprehensive framework for organizing and coordinating AI agents in collaborative software development. By defining clear roles, interaction patterns, and coordination mechanisms, it enables effective teamwork among specialized agents, leading to higher quality outputs and more robust solutions.
## Implementation Status

This feature is **implemented**. See `src/devsynth/adapters/agents/agent_adapter.py` for WSDE team coordination logic.

## References

- [src/devsynth/adapters/agents/agent_adapter.py](../../src/devsynth/adapters/agents/agent_adapter.py)
- [tests/behavior/features/workflow_execution.feature](../../tests/behavior/features/workflow_execution.feature)

## What proofs confirm the solution?
- BDD scenarios in [`tests/behavior/features/wsde_interaction_specification.feature`](../../tests/behavior/features/wsde_interaction_specification.feature) ensure termination and expected outcomes.
- Finite state transitions and bounded loops guarantee termination.
