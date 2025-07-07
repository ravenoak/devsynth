# WSDE-EDRR Integration Architecture

This document describes the architecture of the integration between the WSDE (Workplace, Social, and Democratic Economy) model and the EDRR (Expand-Differentiate-Refine-Retrospect) framework in DevSynth.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DevSynth CLI Interface                        │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    EnhancedEDRRCoordinator                           │
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │  Phase Manager  │  │ Quality Metrics │  │ Micro-Cycle Engine  │  │
│  └────────┬────────┘  └────────┬────────┘  └──────────┬──────────┘  │
│           │                    │                      │             │
│           └──────────┬─────────┴──────────┬──────────┘             │
│                      │                    │                         │
└──────────────────────┼────────────────────┼─────────────────────────┘
                       │                    │
                       ▼                    ▼
┌─────────────────────────────┐  ┌─────────────────────────────────────┐
│        WSDETeam              │  │         Memory System               │
│                             │  │                                     │
│  ┌─────────────────────┐    │  │  ┌─────────────────────────────┐    │
│  │ Role Management     │    │  │  │ Phase-Specific Storage      │    │
│  └─────────────────────┘    │  │  └─────────────────────────────┘    │
│                             │  │                                     │
│  ┌─────────────────────┐    │  │  ┌─────────────────────────────┐    │
│  │ Consensus Building  │    │  │  │ Knowledge Graph Integration │    │
│  └─────────────────────┘    │  │  └─────────────────────────────┘    │
│                             │  │                                     │
│  ┌─────────────────────┐    │  │  ┌─────────────────────────────┐    │
│  │ Dialectical Reasoning│◄──┼──┼──┤ Historical Pattern Retrieval │    │
│  └─────────────────────┘    │  │  └─────────────────────────────┘    │
│                             │  │                                     │
└─────────────────────────────┘  └─────────────────────────────────────┘
           ▲                                       ▲
           │                                       │
           ▼                                       ▼
┌─────────────────────────────┐  ┌─────────────────────────────────────┐
│        Agent Pool           │  │         External Services            │
│                             │  │                                     │
│  ┌─────────────────────┐    │  │  ┌─────────────────────────────┐    │
│  │ Specialized Agents  │    │  │  │ Code Analysis               │    │
│  └─────────────────────┘    │  │  └─────────────────────────────┘    │
│                             │  │                                     │
│  ┌─────────────────────┐    │  │  ┌─────────────────────────────┐    │
│  │ Expertise Profiles  │    │  │  │ Documentation Management    │    │
│  └─────────────────────┘    │  │  └─────────────────────────────┘    │
│                             │  │                                     │
└─────────────────────────────┘  └─────────────────────────────────────┘
```

## Component Descriptions

### EnhancedEDRRCoordinator

The EnhancedEDRRCoordinator is the central component that orchestrates the EDRR process and integrates with the WSDE model. It manages the progression through EDRR phases and coordinates the activities of agents.

**Subcomponents:**
- **Phase Manager**: Controls transitions between EDRR phases
- **Quality Metrics**: Collects and evaluates metrics for phase transitions
- **Micro-Cycle Engine**: Manages iterative refinement within phases

### WSDETeam

The WSDETeam implements the WSDE model for non-hierarchical, context-driven agent collaboration. It manages agent roles, consensus building, and dialectical reasoning.

**Subcomponents:**
- **Role Management**: Assigns and rotates roles based on context
- **Consensus Building**: Facilitates consensus-based decision making
- **Dialectical Reasoning**: Implements thesis-antithesis-synthesis workflow

### Memory System

The Memory System stores and retrieves results, knowledge, and patterns across EDRR phases and cycles.

**Subcomponents:**
- **Phase-Specific Storage**: Stores results for each EDRR phase
- **Knowledge Graph Integration**: Connects with knowledge graphs for enhanced reasoning
- **Historical Pattern Retrieval**: Retrieves patterns from previous cycles

### Agent Pool

The Agent Pool provides specialized agents with different expertise for the WSDE team.

**Subcomponents:**
- **Specialized Agents**: Agents with specific expertise
- **Expertise Profiles**: Profiles defining agent capabilities

### External Services

External Services provide additional capabilities to the EDRR framework.

**Subcomponents:**
- **Code Analysis**: Analyzes code structure and quality
- **Documentation Management**: Manages documentation generation and updates

## Integration Points

### WSDE-EDRR Integration

The integration between the WSDE model and the EDRR framework occurs at several key points:

1. **Phase-Specific Role Assignment**:
   ```python
   # In EnhancedEDRRCoordinator
   def progress_to_phase(self, phase):
       # ...
       self.wsde_team.assign_roles_for_phase(phase, self.task)
       # ...
   ```

2. **Consensus Building for Phase Results**:
   ```python
   # In EnhancedEDRRCoordinator
   def execute_current_phase(self):
       # ...
       consensus = self.wsde_team.build_consensus(task)
       # ...
   ```

3. **Dialectical Reasoning for Solution Refinement**:
   ```python
   # In EnhancedEDRRCoordinator
   def execute_current_phase(self):
       # ...
       if self.current_phase == Phase.REFINE:
           dialectical = self.wsde_team.apply_enhanced_dialectical_reasoning(task, critic_agent)
       # ...
   ```

### Memory Integration

The memory system integrates with both the WSDE model and the EDRR framework:

1. **Phase Result Storage**:
   ```python
   # In EnhancedEDRRCoordinator
   def execute_current_phase(self):
       # ...
       self.memory_manager.store_with_edrr_phase(
           results,
           "EDRR_RESULTS",
           self.current_phase.value,
           {"cycle_id": self.cycle_id}
       )
       # ...
   ```

2. **Knowledge Retrieval for Dialectical Reasoning**:
   ```python
   # In WSDETeam
   def apply_enhanced_dialectical_reasoning_with_knowledge(self, task, critic_agent, external_knowledge):
       # ...
       relevant_knowledge = self._identify_relevant_knowledge(task, solution, external_knowledge)
       # ...
   ```

## Data Flow

1. **CLI to Coordinator**: The CLI interface initiates an EDRR cycle by calling the EnhancedEDRRCoordinator.
2. **Coordinator to WSDE Team**: The coordinator assigns roles to the WSDE team based on the current phase.
3. **WSDE Team to Agents**: The WSDE team delegates tasks to agents based on their expertise.
4. **Agents to WSDE Team**: Agents return solutions to the WSDE team.
5. **WSDE Team to Coordinator**: The WSDE team returns consensus results to the coordinator.
6. **Coordinator to Memory**: The coordinator stores results in the memory system.
7. **Memory to WSDE Team**: The memory system provides knowledge and patterns to the WSDE team for dialectical reasoning.
8. **Coordinator to CLI**: The coordinator returns the final report to the CLI interface.

## Configuration

The integration between the WSDE model and the EDRR framework can be configured through the coordinator's configuration:

```python
config = {
    "edrr": {
        "quality_based_transitions": True,
        "phase_transition": {
            "auto": True
        },
        "wsde_integration": {
            "enable_dialectical_reasoning": True,
            "enable_consensus_building": True,
            "enable_peer_review": True
        }
    }
}
```

## Conclusion

The integration between the WSDE model and the EDRR framework provides a powerful approach to problem-solving in DevSynth. By combining the non-hierarchical, context-driven collaboration of the WSDE model with the structured phases of the EDRR framework, DevSynth enables more effective and efficient problem-solving.