---

author: DevSynth Team
date: '2025-07-07'
last_reviewed: "2025-07-10"
status: published
tags:

- technical-reference

title: EDRR Framework Usage Guide
version: "0.1.0-alpha.1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Technical Reference</a> &gt; EDRR Framework Usage Guide
</div>

# EDRR Framework Usage Guide

## Overview

The EDRR (EDRR) framework is a structured approach to problem-solving and development in DevSynth. This document provides a comprehensive guide to the EDRR framework, including its phases, components, and integration with the WSDE model.

> **Note**: This documentation reflects the enhanced EDRR framework implementation from Phase 3, which includes improved micro-cycle implementation, enhanced phase transitions with quality metrics, and seamless integration with the WSDE model.

## EDRR Phases

The EDRR framework consists of four distinct phases, each with a specific purpose and set of activities:

### 1. Expand Phase

The Expand phase focuses on exploration and idea generation. During this phase, agents brainstorm approaches, gather requirements, and explore potential solutions without judgment.

**Key Activities:**

- Brainstorming multiple approaches
- Gathering requirements and constraints
- Exploring the problem space
- Generating diverse ideas


### 2. Differentiate Phase

The Differentiate phase involves analysis and evaluation of the ideas generated during the Expand phase. Agents compare approaches, identify trade-offs, and select the most promising solution.

**Key Activities:**

- Comparing different approaches
- Analyzing trade-offs
- Evaluating feasibility and effectiveness
- Selecting the most promising solution


### 3. Refine Phase

The Refine phase focuses on implementation and optimization. Agents develop the selected solution, address issues, and optimize for quality.

**Key Activities:**

- Implementing the selected approach
- Addressing edge cases and issues
- Optimizing for performance, security, and maintainability
- Testing and validation


### 4. Retrospect Phase

The Retrospect phase involves reflection and learning. Agents evaluate the implementation, identify lessons learned, and generate insights for future work.

**Key Activities:**

- Evaluating the implementation
- Identifying lessons learned
- Documenting insights and patterns
- Generating recommendations for future work


## Implementation Components

### EnhancedEDRRCoordinator

The `EnhancedEDRRCoordinator` class is the core implementation of the EDRR framework. It manages the progression through EDRR phases and coordinates the activities of agents.

```python
from devsynth.application.EDRR.edrr_coordinator_enhanced import EnhancedEDRRCoordinator

# Create a coordinator

coordinator = EnhancedEDRRCoordinator(
    memory_manager=memory_manager,
    wsde_team=wsde_team,
    code_analyzer=code_analyzer,
    ast_transformer=ast_transformer,
    prompt_manager=prompt_manager,
    documentation_manager=documentation_manager,
    config=config
)
```

## Phase Transitions

The EDRR framework includes mechanisms for transitioning between phases:

- `progress_to_phase(phase)`: Progresses to a specific phase
- `progress_to_next_phase()`: Progresses to the next phase in sequence
- `_enhanced_maybe_auto_progress()`: Automatically progresses based on quality metrics


### Enhanced Phase Transition Logic

The enhanced EDRR framework includes sophisticated phase transition logic:

```python
def _enhanced_maybe_auto_progress(self):
    """Enhanced version of auto-progress with quality-based transitions."""
    # Prevent re-entry during active transition
    if self._transition_in_progress:
        return False

    self._transition_in_progress = True
    try:
        # Check if auto-progress is enabled
        if not self.config["EDRR"]["phase_transition"]["auto"]:
            return False

        # Check if quality-based transitions are enabled
        if not self.config["EDRR"]["quality_based_transitions"]:
            return self._legacy_maybe_auto_progress()

        # Assess the quality of the current phase
        quality_assessment = self._assess_phase_quality()

        # Check if we can progress based on quality
        if quality_assessment["can_progress"]:
            # Get the next phase
            next_phase = self._get_next_phase()
            if next_phase:
                # Progress to the next phase
                self.progress_to_phase(next_phase)
                return True

        return False
    finally:
        self._transition_in_progress = False
```

This enhanced implementation includes:

1. **Guard Against Re-entry**: Prevents infinite loops during phase transitions
2. **Maximum Iteration Count**: Limits the number of automatic transitions
3. **Quality-Based Decision Making**: Uses quality metrics to determine when to transition


### Quality Metrics and Collection

The enhanced EDRR framework uses sophisticated quality metrics to determine when to transition between phases:

```python

# Quality thresholds for phase transitions

quality_thresholds = {
    Phase.EXPAND: 0.7,
    Phase.DIFFERENTIATE: 0.8,
    Phase.REFINE: 0.85,
    Phase.RETROSPECT: 0.9
}

def _assess_phase_quality(self, phase=None):
    """Assess the quality of a phase's results."""
    if phase is None:
        phase = self.current_phase

    # Get the phase results
    phase_results = self.results.get(phase, {})

    # Collect metrics for the phase
    metrics = self.phase_metrics.collect_metrics(phase, phase_results)

    # Calculate a quality score based on the metrics
    quality_score = self.phase_metrics.calculate_quality_score(phase, metrics)

    # Determine if we can progress based on the quality score
    can_progress = quality_score >= self.quality_thresholds.get(phase, 0.7)

    return {
        "quality": quality_score,
        "can_progress": can_progress,
        "metrics": metrics
    }
```

## Metrics Collection During Transitions

The enhanced EDRR framework collects detailed metrics during phase transitions:

```python
def progress_to_phase(self, phase):
    """Progress to a specific phase."""
    # Collect metrics for the current phase before transitioning
    if self.current_phase:
        metrics = self.phase_metrics.collect_metrics(
            self.current_phase,
            self.results.get(self.current_phase, {})
        )
        self.phase_metrics.store_metrics(self.current_phase, metrics)

    # Transition to the new phase
    self.current_phase = phase

    # Initialize metrics for the new phase
    self.phase_metrics.initialize_metrics(phase)

    # Assign roles based on the new phase
    self.wsde_team.assign_roles_for_phase(phase, self.task)
```

This metrics collection enables data-driven decisions about phase transitions and provides valuable insights for retrospective analysis.

## Integration with WSDE Model

The EDRR framework integrates with the WSDE model to provide a comprehensive approach to problem-solving.

### Enhanced WSDE-EDRR Integration

The enhanced EDRR framework includes deep integration with the WSDE model:

```python

# Create an enhanced EDRR coordinator with WSDE integration

coordinator = EnhancedEDRRCoordinator(
    memory_manager=memory_manager,
    wsde_team=wsde_team,  # WSDE team is a core component
    code_analyzer=code_analyzer,
    ast_transformer=ast_transformer,
    prompt_manager=prompt_manager,
    documentation_manager=documentation_manager,
    config=config
)
```

This integration enables:

1. **Phase-Specific Expertise Utilization**: Leveraging the right expertise for each phase
2. **Collaborative Problem-Solving**: Multiple agents working together on complex tasks
3. **Dialectical Improvement**: Continuous improvement through thesis-antithesis-synthesis
4. **Consensus-Based Decision Making**: Incorporating diverse perspectives in decisions


## Phase-Specific Role Assignment

As the EDRR framework progresses through phases, the WSDE model assigns roles based on the current phase:

```python

# In EnhancedEDRRCoordinator

def progress_to_phase(self, phase):
    # ...
    self.wsde_team.assign_roles_for_phase(phase, self.task)
    # ...
```

## Phase-Specific Expertise Mapping

The EDRR framework uses a mapping of expertise to phases to ensure the right agents lead each phase:

```python

# In WSDETeam

def assign_roles_for_phase(self, phase, task):
    """Assign roles based on the current EDRR phase."""
    # Get expertise relevant to the current phase
    phase_expertise = self.PHASE_EXPERTISE_MAP.get(phase, [])

    # Create a task with phase-specific requirements
    phase_task = {**task, "required_expertise": phase_expertise}

    # Select the Primus based on phase-specific expertise
    self.select_primus_by_expertise(phase_task)

    # Assign other roles
    self.assign_roles()
```

## Dialectical Reasoning in EDRR Phases

The EDRR framework leverages the WSDE model's dialectical reasoning capabilities in each phase:

```python

# In EnhancedEDRRCoordinator

def _execute_expand_phase(self):
    # Get initial approaches from the WSDE team
    approaches = self.wsde_team.process(self.task)

    # Apply dialectical reasoning to improve approaches
    improved_approaches = self.wsde_team.apply_enhanced_dialectical_reasoning(
        self.task, approaches
    )

    return improved_approaches
```

## Micro-Cycles with WSDE Collaboration

The enhanced EDRR framework supports micro-cycles with WSDE team collaboration:

```python

# In EnhancedEDRRCoordinator

def _execute_micro_cycle(self, phase, iteration):
    """Execute a micro-cycle within the current phase."""
    # Create a micro-cycle task
    micro_task = self._create_micro_cycle_task(phase, iteration)

    # Delegate to WSDE team
    wsde_results = self.wsde_team.process(micro_task)

    # Apply dialectical reasoning to improve results
    improved_results = self.wsde_team.apply_enhanced_dialectical_reasoning(
        micro_task, wsde_results
    )

    # Aggregate results
    aggregated_results = self._aggregate_micro_cycle_results(
        phase, iteration, improved_results
    )

    return aggregated_results
```

## Error Handling and Recovery

The enhanced EDRR framework includes error handling and recovery mechanisms for WSDE team integration:

```python

# In EnhancedEDRRCoordinator

def execute_current_phase(self):
    """Execute the current phase with error handling."""
    try:
        # Execute the phase
        results = self._execute_phase(self.current_phase)
        return results
    except Exception as e:
        # Handle the error
        error_info = {
            "error": str(e),
            "phase": self.current_phase,
            "timestamp": self._get_timestamp()
        }

        # Attempt recovery
        recovery_result = self._attempt_recovery(e, self.current_phase)

        # Return error information and recovery result
        return {
            "error": error_info,
            "recovery": recovery_result
        }
```

## Enhanced Micro-Cycle Implementation

The enhanced EDRR framework includes significant improvements to the micro-cycle implementation:

1. **Nested Micro-Cycles**: Support for nested micro-cycles with proper result aggregation
2. **Sophisticated Termination Conditions**: Multiple factors for determining when to terminate micro-cycles
3. **Result Aggregation**: Improved aggregation of results from multiple micro-cycles
4. **Conflict Resolution**: Better merging of complementary approaches from different micro-cycles


```python

# Configure micro-cycles

config = {
    "EDRR": {
        "micro_cycles": {
            "enabled": True,
            "max_iterations": 3,
            "quality_threshold": 0.85,
            "convergence_threshold": 0.05,
            "termination_factors": ["quality", "convergence", "iterations"]
        }
    }
}

# Create a coordinator with micro-cycles enabled

coordinator = EnhancedEDRRCoordinator(
    # Required parameters...
    config=config
)

# Execute the current phase with micro-cycles

results = coordinator.execute_current_phase()
```

## Termination Condition System

The enhanced micro-cycle implementation includes a sophisticated termination condition system:

```python
def _should_continue_micro_cycles(self, phase, iteration, results):
    """Determine if micro-cycles should continue."""
    # Check maximum iterations
    if iteration >= self.config["EDRR"]["micro_cycles"]["max_iterations"]:
        return False

    # Check quality threshold
    quality = self._assess_result_quality(results)
    if quality >= self.config["EDRR"]["micro_cycles"]["quality_threshold"]:
        return False

    # Check convergence
    if iteration > 1 and self._check_convergence(results, self._previous_results):
        return False

    return True
```

This system tracks multiple termination factors with severity levels, considers combinations of factors for termination decisions, and provides detailed explanations of termination reasons.

## CLI Integration

The EDRR framework is integrated with the DevSynth CLI through the `EDRR-cycle` command:

```bash

# Run from a manifest file

devsynth EDRR-cycle --manifest .devsynth/project.yaml

# Run from a prompt

devsynth EDRR-cycle --prompt "Improve error handling in the API endpoints"

# Run with additional context

devsynth EDRR-cycle --prompt "Optimize database queries" --context "Focus on reducing N+1 queries"

# Control the maximum number of iterations

devsynth EDRR-cycle --prompt "Refactor the authentication system" --max-iterations 5

# Disable automatic phase transitions

devsynth EDRR-cycle --prompt "Implement authentication" --auto false
```

## Usage Patterns

### Basic Usage

```python
from devsynth.application.EDRR.edrr_coordinator_enhanced import EnhancedEDRRCoordinator
from devsynth.methodology.base import Phase

# Create a coordinator

coordinator = EnhancedEDRRCoordinator(
    # Required parameters...
)

# Start a cycle

task = {"description": "Implement a feature"}
coordinator.start_cycle(task)

# Execute the current phase

results = coordinator.execute_current_phase()

# Progress to the next phase

coordinator.progress_to_next_phase()

# Execute the next phase

results = coordinator.execute_current_phase()

# Generate a report

report = coordinator.generate_report()
```

## Automatic Phase Transitions

```python

# Configure automatic phase transitions

config = {
    "EDRR": {
        "quality_based_transitions": True,
        "phase_transition": {
            "auto": True
        }
    }
}

coordinator = EnhancedEDRRCoordinator(
    # Required parameters...
    config=config
)

# Start a cycle

coordinator.start_cycle(task)

# Execute the current phase

# The coordinator will automatically progress to the next phase if quality thresholds are met

results = coordinator.execute_current_phase()
```

## Manual Phase Control

```python

# Configure manual phase transitions

config = {
    "EDRR": {
        "phase_transition": {
            "auto": False
        }
    }
}

coordinator = EnhancedEDRRCoordinator(
    # Required parameters...
    config=config
)

# Start a cycle

coordinator.start_cycle(task)

# Execute each phase manually

for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
    coordinator.progress_to_phase(phase)
    results = coordinator.execute_current_phase()
```

## Advanced Features

### Phase Metrics

The enhanced EDRR framework collects metrics for each phase to evaluate quality and progress:

```python

# Get metrics for the current phase

metrics = coordinator.phase_metrics.get_metrics(coordinator.current_phase)

# Get all metrics

all_metrics = coordinator.phase_metrics.get_all_metrics()
```

## Micro-Cycle Termination

The EDRR framework includes sophisticated termination conditions for micro-cycles:

```python

# Configure termination conditions

termination_conditions = {
    "max_iterations": 5,
    "quality_threshold": 0.9,
    "convergence_threshold": 0.05
}

# Execute a micro-cycle with termination conditions

results = coordinator.execute_micro_cycle(context, termination_conditions)
```

## Memory Integration

The EDRR framework integrates with the memory system to store and retrieve results:

```python

# Store results in memory

memory_id = coordinator.memory_manager.store_with_edrr_phase(
    results,
    "EDRR_RESULTS",
    coordinator.current_phase.value,
    {"cycle_id": coordinator.cycle_id}
)

# Retrieve results from memory

previous_results = coordinator.memory_manager.retrieve_with_edrr_phase(
    "EDRR_RESULTS",
    Phase.EXPAND.value,
    {"cycle_id": coordinator.cycle_id}
)
```

## Best Practices

1. **Phase-Specific Expertise**: Assign agents with relevant expertise to each phase.
2. **Quality Metrics**: Define appropriate quality thresholds for phase transitions.
3. **Micro-Cycles**: Use micro-cycles for iterative refinement within phases.
4. **Memory Integration**: Store and retrieve results from memory for continuity.
5. **Comprehensive Reports**: Generate detailed reports for analysis and learning.


## Conclusion

The EDRR framework provides a structured approach to problem-solving and development in DevSynth. By integrating with the WSDE model and leveraging quality-based phase transitions, it enables more effective and efficient problem-solving.
## Implementation Status

.
