---

author: DevSynth Team
date: '2025-07-07'
last_reviewed: "2025-07-10"
status: published
tags:

- technical-reference

title: WSDE Model Implementation Guide
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Technical Reference</a> &gt; WSDE Model Implementation Guide
</div>

# WSDE Model Implementation Guide

## Overview

The Workplace, Social, and Democratic Economy (WSDE) model is a non-hierarchical, context-driven agent collaboration framework implemented in DevSynth. This document provides a comprehensive guide to the WSDE model implementation, including its core concepts, components, usage patterns, and integration with the EDRR framework.

> **Note**: This documentation reflects the enhanced WSDE model implementation from Phase 3, which includes Context-Driven Leadership, improved Dialectical Reasoning, and seamless integration with the EDRR framework.

## Core Concepts

### Non-Hierarchical Collaboration

The WSDE model is designed to enable non-hierarchical collaboration among agents. Unlike traditional hierarchical models where authority flows from top to bottom, the WSDE model treats all agents as peers with equal status. This approach allows for more flexible and adaptive collaboration, where leadership emerges based on context and expertise rather than fixed roles.

### Context-Driven Leadership

In the WSDE model, leadership is context-driven. The agent with the most relevant expertise for a given task becomes the temporary Primus (leader). This role rotates based on the task context, ensuring that the most qualified agent leads each phase of work. This approach maximizes the collective intelligence of the team by leveraging each agent's strengths.

#### Enhanced Expertise Scoring

The enhanced WSDE model includes sophisticated expertise scoring that considers multiple factors:

```python
def calculate_expertise_score(agent, task):
    """Calculate an expertise score for an agent based on the task."""
    base_score = _calculate_base_expertise_score(agent, task)
    experience_factor = _calculate_experience_factor(agent, task)
    performance_factor = _calculate_performance_factor(agent, task)
    context_factor = _calculate_context_factor(agent, task)

    return base_score * experience_factor * performance_factor * context_factor
```

Factors considered in expertise scoring include:

- **Base Expertise**: Direct match between agent expertise and task requirements
- **Experience**: Agent's historical experience with similar tasks
- **Past Performance**: Agent's success rate on similar tasks
- **Task Context**: Contextual factors such as domain, complexity, and phase


#### Dynamic Role Switching

The enhanced WSDE model supports dynamic role switching based on task context:

```python

# Select Primus based on task context

team.select_primus_by_expertise(task)

# Assign roles based on current Primus

team.assign_roles()

# Later, when task context changes

team.select_primus_by_expertise(new_task)
team.assign_roles()
```

This dynamic role switching ensures that leadership adapts to changing requirements throughout the development process.

## Dialectical Reasoning

The WSDE model incorporates dialectical reasoning to improve solution quality. This process involves:

1. **Thesis**: An initial solution or proposal
2. **Antithesis**: Critical evaluation and identification of weaknesses
3. **Synthesis**: A refined solution that addresses the identified weaknesses


This dialectical process ensures that solutions are thoroughly examined and improved through critical thinking.

### Consensus Building

Decision-making in the WSDE model is based on consensus rather than authority. All agents contribute to decisions, and the final outcome reflects input from all relevant agents. This approach leads to more robust decisions that incorporate diverse perspectives.

## Implementation Components

### WSDETeam Class

The `WSDETeam` class is the core implementation of the WSDE model. It manages a team of agents and coordinates their collaboration.

```python
from devsynth.domain.models.WSDE import WSDETeam

# Create a team

team = WSDETeam()

# Add agents to the team

team.add_agent(agent1)
team.add_agent(agent2)
```

## Role Management

The WSDE model includes several methods for managing agent roles:

- `rotate_primus()`: Rotates the Primus role to the next agent
- `select_primus_by_expertise(task)`: Selects the Primus based on task context
- `assign_roles()`: Assigns WSDE roles to agents
- `get_agent_by_role(role)`: Gets an agent with a specific role


### Collaboration Methods

The WSDE model provides methods for agent collaboration:

- `build_consensus(task)`: Builds consensus among agents for a task
- `vote_on_critical_decision(task)`: Conducts a vote on a critical decision
- `apply_enhanced_dialectical_reasoning(task, critic_agent)`: Applies dialectical reasoning to improve a solution


## Integration with EDRR Framework

The WSDE model integrates with the EDRR (EDRR) framework to provide a comprehensive approach to problem-solving.

### Phase-Specific Role Assignment

The WSDE model assigns roles based on the current EDRR phase:

```python
team.assign_roles_for_phase(phase, task)
```

This method ensures that agents with the most relevant expertise for each phase are assigned appropriate roles.

#### Expertise Mapping for EDRR Phases

The enhanced WSDE model includes a sophisticated mapping of expertise to EDRR phases:

```python
PHASE_EXPERTISE_MAP = {
    Phase.EXPAND: ["exploration", "brainstorming", "creativity", "ideation"],
    Phase.DIFFERENTIATE: ["analysis", "comparison", "evaluation", "critical thinking"],
    Phase.REFINE: ["implementation", "coding", "development", "optimization"],
    Phase.RETROSPECT: ["evaluation", "reflection", "learning", "improvement"]
}
```

This mapping is used to select the most appropriate agent for the Primus role in each phase.

### Dynamic Role Reassignment

As the EDRR framework progresses through phases, the WSDE model dynamically reassigns roles to ensure optimal collaboration:

```python
team._assign_roles_for_edrr_phase(phase, task)
```

The enhanced implementation includes:

1. **Phase-Specific Primus Selection**: Selects a Primus with expertise relevant to the current phase
2. **Role Rotation**: Ensures that all agents have an opportunity to serve in different roles
3. **Expertise Weighting**: Weights expertise scores based on phase requirements
4. **Context Preservation**: Maintains context across phase transitions


### Quality-Based Phase Transitions

The WSDE team contributes to quality-based phase transitions in the EDRR framework:

```python

# In EnhancedEDRRCoordinator

def _assess_phase_quality(self, phase=None):
    if phase is None:
        phase = self.current_phase

    # Get results from the WSDE team
    wsde_results = self.wsde_team.evaluate_phase_quality(phase, self.results.get(phase, {}))

    # Combine with other quality metrics
    quality_score = self._calculate_combined_quality(wsde_results, phase)

    return {
        "quality": quality_score,
        "can_progress": quality_score >= self.quality_thresholds.get(phase, 0.7)
    }
```

## Micro-Cycle Collaboration

The WSDE team collaborates on micro-cycles within each EDRR phase:

```python

# In EnhancedEDRRCoordinator

def _execute_micro_cycle(self, phase, iteration):
    # Create a micro-cycle task
    micro_task = self._create_micro_cycle_task(phase, iteration)

    # Delegate to WSDE team
    wsde_results = self.wsde_team.process(micro_task)

    # Apply dialectical reasoning to improve results
    improved_results = self.wsde_team.apply_enhanced_dialectical_reasoning(micro_task, wsde_results)

    return improved_results
```

## Usage Patterns

### Basic Usage

```python
from devsynth.domain.models.WSDE import WSDETeam
from devsynth.application.agents.unified_agent import UnifiedAgent

# Create a team

team = WSDETeam()

# Add agents to the team

team.add_agents([agent1, agent2, agent3])

# Assign roles

team.assign_roles()

# Process a task

task = {"description": "Implement a feature", "domain": "coding"}
team.select_primus_by_expertise(task)

# Build consensus

consensus = team.build_consensus(task)
```

## Integration with EDRR

```python
from devsynth.application.EDRR.edrr_coordinator_enhanced import EnhancedEDRRCoordinator
from devsynth.domain.models.WSDE import WSDETeam

# Create a team

team = WSDETeam()
team.add_agents([agent1, agent2, agent3])

# Create an EDRR coordinator

coordinator = EnhancedEDRRCoordinator(
    wsde_team=team,
    # Other required parameters...
)

# Start a cycle

task = {"description": "Implement a feature"}
coordinator.start_cycle(task)

# Progress through phases

coordinator.progress_to_phase(Phase.DIFFERENTIATE)
```

## Advanced Features

### Peer Review Mechanism

The WSDE model includes a peer review mechanism for quality assurance:

```python
review = team.request_peer_review(work_product, author, reviewer_agents)
feedback = team.conduct_peer_review(work_product, author, reviewer_agents)
```

### Weighted Voting

For critical decisions, the WSDE model supports weighted voting based on expertise:

```python
result = team._apply_weighted_voting(task, voting_result, domain)
```

### Multi-Disciplinary Dialectical Reasoning

For complex problems requiring multiple disciplines, the WSDE model provides enhanced dialectical reasoning:

```python
result = team.apply_multi_disciplinary_dialectical_reasoning(
    task, critic_agent, disciplinary_knowledge, disciplinary_agents
)
```

## Best Practices

1. **Diverse Expertise**: Include agents with diverse expertise in the team to maximize collective intelligence.
2. **Task Context**: Provide detailed task context to enable effective Primus selection.
3. **Phase-Specific Roles**: Use phase-specific role assignment for optimal EDRR integration.
4. **Dialectical Improvement**: Apply dialectical reasoning to improve solution quality.
5. **Consensus Building**: Use consensus building for important decisions to incorporate diverse perspectives.


## Conclusion

The WSDE model provides a powerful framework for non-hierarchical, context-driven agent collaboration. By leveraging the collective intelligence of diverse agents and incorporating dialectical reasoning, it enables more robust and adaptive problem-solving.
## Implementation Status

The peer review mechanism is fully implemented and covered by integration tests.
