---

title: "EDRR Specification"
date: "2025-06-01"
version: "0.1.0-alpha.1"
tags:
  - "EDRR"
  - "specification"
  - "methodology"
  - "workflow"

references:
  - "Cormen, T. H., C. E. Leiserson, R. L. Rivest, and C. Stein. Introduction to Algorithms. 4th ed., MIT Press, 2022."

status: "published"
author: "DevSynth Team"
last_reviewed: "2025-07-10"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Specifications</a> &gt; EDRR Specification
</div>

# EDRR Specification

## Executive Summary

The EDRR (Expand, Differentiate, Refine, Retrospect) cycle is a structured workflow methodology implemented in DevSynth to guide the iterative development process. This specification defines the components, interactions, and implementation details of the EDRR, including its recursive architecture, integration with other system components, and implementation guidelines. The EDRR framework enables self-optimization at multiple levels of granularity, creating a more adaptive and intelligent development process.

## Table of Contents

- [1. Overview](#1-overview)
- [2. Purpose and Goals](#2-purpose-and-goals)
- [3. EDRR Stages](#3-EDRR-cycle-stages)
  - [3.1 Expand](#31-expand)
  - [3.2 Differentiate](#32-differentiate)
  - [3.3 Refine](#33-refine)
  - [3.4 Retrospect](#34-retrospect)
- [4. Integration with Other Components](#4-integration-with-other-components)
- [5. Implementation Guidelines](#5-implementation-guidelines)
- [6. Recursive EDRR Architecture](#6-recursive-EDRR-architecture)
- [7. EDRR Coordinator](#7-EDRR-coordinator)
- [8. EDRR Manifest](#8-EDRR-manifest)
- [9. Testing and Validation](#9-testing-and-validation)
- [10. References](#10-references)


## 1. Overview

The EDRR (Expand, Differentiate, Refine, Retrospect) cycle is a structured workflow methodology implemented in DevSynth to guide the iterative development process. This specification defines the components, interactions, and implementation details of the EDRR.

The EDRR framework is implemented as a recursive, fractal structure where each macro-level phase (Expand, Differentiate, Refine, Retrospect) contains its own nested micro-EDRR cycles. This recursive approach enables self-optimization at multiple levels of granularity, creating a more adaptive and intelligent development process.

## 2. Purpose and Goals

The EDRR aims to:

1. Provide a systematic approach to iterative development
2. Enable continuous improvement of artifacts through structured feedback
3. Support multi-agent collaboration with clear role definitions
4. Ensure comprehensive exploration of problem spaces before narrowing solutions
5. Facilitate learning from past iterations to improve future performance


## 3. EDRR Stages

### 3.1 Expand

**Purpose**: Broaden the exploration space to consider multiple approaches, perspectives, and possibilities.

**Activities**:

- Generate diverse solution candidates
- Explore alternative approaches
- Consider edge cases and potential challenges
- Gather relevant context and information


**Outputs**:

- Collection of potential approaches
- Expanded context information
- Identified constraints and requirements
- Preliminary evaluation criteria


**Implementation**:

- Divergent thinking prompts for agents
- Context retrieval from Memory System
- Parallel exploration by multiple agents
- Structured brainstorming protocols
- DeepAgents planning tools integration (`write_todos` for systematic task decomposition)
- Hierarchical task breakdown with subagent spawning capabilities


### 3.2 Differentiate

**Purpose**: Analyze and categorize the expanded options, identifying strengths, weaknesses, and unique characteristics.

**Activities**:

- Compare and contrast approaches
- Evaluate options against requirements
- Identify trade-offs and dependencies
- Prioritize approaches based on criteria


**Outputs**:

- Comparative analysis of options
- Evaluation matrix with scoring
- Categorized approaches
- Prioritized list of candidates


**Implementation**:

- Structured comparison frameworks
- Multi-criteria decision analysis
- Dialectical reasoning patterns
- Collaborative evaluation by agent teams


### 3.3 Refine

**Purpose**: Improve selected approaches through iteration, combination, and enhancement.

**Activities**:

- Develop detailed implementations
- Combine strengths from multiple approaches
- Address identified weaknesses
- Optimize for performance and quality


**Outputs**:

- Refined solution implementations
- Detailed specifications
- Optimized artifacts
- Validation results


**Implementation**:

- Iterative improvement loops
- Targeted enhancement prompts
- Quality validation checks
- Progressive refinement protocols


### 3.4 Retrospect

**Purpose**: Review the process and outcomes to capture learnings and improve future iterations.

**Activities**:

- Analyze the effectiveness of the process
- Document lessons learned
- Update knowledge base with new insights
- Identify process improvements


**Outputs**:

- Process evaluation report
- Captured learnings
- Updated best practices
- Improvement recommendations


**Implementation**:

- Structured reflection prompts
- Performance metrics analysis
- Knowledge base updates
- Process adaptation mechanisms


## 4. Integration with Other Components

### 4.1 WSDE Model Integration

The EDRR works in conjunction with the WSDE (WSDE) model:

- **Primus**: Coordinates the overall EDRR process and ensures alignment with goals
- **Worker**: Executes specific tasks within each EDRR stage
- **Supervisor**: Monitors progress and ensures quality across the EDRR
- **Designer**: Focuses on creative aspects during Expand and Refine stages
- **Evaluator**: Leads the Differentiate and Retrospect stages


### 4.2 Memory System Integration

The EDRR leverages the hybrid memory system:

- **Vector Store**: Retrieves relevant examples and context during Expand stage
- **Structured Store**: Maintains metadata about artifacts through the cycle
- **Graph Store**: Tracks relationships between artifacts and their evolution


### 4.3 Workflow Orchestration

The orchestration layer manages the EDRR execution:

- Defines transition conditions between stages
- Handles parallel and sequential execution of tasks
- Manages state persistence across the cycle
- Coordinates human intervention points


## 4.4 Recursive EDRR Structure

The EDRR implements a recursive, fractal structure where each macro phase contains its own nested micro-EDRR cycles:

### 4.4.1 Micro-EDRR within Macro-Expand

The Macro-Expand phase is executed through a nested micro-EDRR:

- **Micro-Expand**: Broad exploration of potential solutions, approaches, and ideas. Agents generate diverse solution candidates, explore alternative approaches, and gather relevant context.
- **Micro-Differentiate**: Analysis and categorization of the expanded options. Agents compare approaches, evaluate options against requirements, and prioritize based on criteria.
- **Micro-Refine**: Improvement of selected approaches. Agents develop initial prototypes, draft data cleaning pipelines, and test initial prompt templates.
- **Micro-Retrospect**: Review of early exploration results. Agents analyze performance metrics, identify misalignments, and document lessons learned.


### 4.4.2 Micro-EDRR within Macro-Differentiate

The Macro-Differentiate phase is realized through its own internal micro-EDRR:

- **Micro-Expand**: Exploration of architectural patterns and model options. Agents survey software architecture patterns, LLM models, and analyze trade-offs.
- **Micro-Differentiate**: Selection of patterns and design of interfaces. Agents select optimal architectural patterns, design API specifications, and apply prompt engineering principles.
- **Micro-Refine**: Detailed design and proof-of-concept implementation. Agents generate detailed specifications, conduct small-scale proofs-of-concept, and generate unit tests.
- **Micro-Retrospect**: Architectural review and refinement. Agents review architectural decisions, evaluate trade-offs, and identify areas for improvement.


### 4.4.3 Micro-EDRR within Macro-Refine

The iterative Macro-Refine phase is manifested through its own internal micro-EDRR:

- **Micro-Expand**: Exploration of implementation approaches. Agents explore fine-tuning methodologies, prompt engineering strategies, and generate test cases.
- **Micro-Differentiate**: Selection of specific approaches and task decomposition. Agents select fine-tuning approaches, prioritize test cases, and decompose complex tasks.
- **Micro-Refine**: Core implementation loop. Agents write code, generate tests, apply optimizations, and debug errors in an iterative process.
- **Micro-Retrospect**: Iteration review and quality assessment. Agents assess code quality, evaluate fine-tuning effectiveness, and analyze debugging history.


### 4.4.4 Micro-EDRR within Macro-Retrospect

The continuous Macro-Retrospect phase is managed through its own iterative micro-EDRR:

- **Micro-Expand**: Exploration of development process improvements and best practices. Agents explore new development techniques, brainstorm quality indicators, and scan for potential process enhancements.
- **Micro-Differentiate**: Design of evaluation frameworks and formulation of guidelines. Agents design quality assessment frameworks, define development KPIs, and draft coding standards.
- **Micro-Refine**: Implementation of process improvements and guideline updates. Agents implement development workflows, refine feedback collection, and update coding standards.
- **Micro-Retrospect**: Meta-retrospective on development process effectiveness. Agents review the development workflow's effectiveness and the coding standards' adaptability.


### 4.4.5 Delimiting Principles for Recursion

To prevent unbounded recursion and ensure efficient operation, the following principles determine when EDRR recursion should end:

1. **Granularity Threshold**: Recursion ceases when the level of detail is sufficient for the current objective and further subdivision would be counterproductive.
2. **Cost-Benefit Analysis**: Recursion terminates when the marginal benefit of further iteration no longer justifies the computational cost.
3. **Quality Thresholds**: Recursion ends when predefined quality metrics (accuracy, performance, coverage) meet or exceed target thresholds.
4. **Resource Limits**: Hard limits on recursion depth, time, or computational resources prevent excessive iteration.
5. **Human Judgment**: Strategic human oversight provides the ultimate decision on when recursion should terminate, especially for subjective evaluations or high-stakes decisions.


## 5. Implementation Details

### 5.1 Coordinator Component

```python
class EDRRCoordinator:
    """Manages the execution of the EDRR with recursive capabilities."""

    def __init__(self, memory_manager, agent_registry, workflow_engine):
        self.memory_manager = memory_manager
        self.agent_registry = agent_registry
        self.workflow_engine = workflow_engine
        self.current_stage = None
        self.cycle_context = {}
        self.recursion_depth = 0
        self.max_recursion_depth = 3  # Configurable
        self.parent_coordinator = None  # For nested cycles

    def start_cycle(self, initial_context, parent_coordinator=None):
        """Begin a new EDRR with the provided context."""
        self.cycle_context = initial_context
        self.current_stage = "expand"
        self.parent_coordinator = parent_coordinator

        if parent_coordinator:
            self.recursion_depth = parent_coordinator.recursion_depth + 1

        # Check recursion depth limits
        if self.recursion_depth > self.max_recursion_depth:
            return {"status": "recursion_limit_reached", "context": self.cycle_context}

        return self.execute_expand()

    def execute_expand(self):
        """Execute the Expand stage of the EDRR."""
        # Create a micro-EDRR for the Expand phase
        micro_cycle = self._create_micro_cycle("expand")
        expand_results = micro_cycle.start_cycle(self.cycle_context, self)

        # Update context with results
        self.cycle_context.update(expand_results)

        return self.transition_to_next_stage(expand_results)

    def execute_differentiate(self, expand_results):
        """Execute the Differentiate stage of the EDRR."""
        # Create a micro-EDRR for the Differentiate phase
        micro_cycle = self._create_micro_cycle("differentiate")
        differentiate_results = micro_cycle.start_cycle(expand_results, self)

        # Update context with results
        self.cycle_context.update(differentiate_results)

        return self.transition_to_next_stage(differentiate_results)

    def execute_refine(self, differentiate_results):
        """Execute the Refine stage of the EDRR."""
        # Create a micro-EDRR for the Refine phase
        micro_cycle = self._create_micro_cycle("refine")
        refine_results = micro_cycle.start_cycle(differentiate_results, self)

        # Update context with results
        self.cycle_context.update(refine_results)

        return self.transition_to_next_stage(refine_results)

    def execute_retrospect(self, refine_results):
        """Execute the Retrospect stage of the EDRR."""
        # Create a micro-EDRR for the Retrospect phase
        micro_cycle = self._create_micro_cycle("retrospect")
        retrospect_results = micro_cycle.start_cycle(refine_results, self)

        # Update context with results
        self.cycle_context.update(retrospect_results)

        return {"status": "completed", "context": self.cycle_context}

    def _create_micro_cycle(self, phase_type):
        """Create a micro-EDRR coordinator for a specific phase."""
        # Configure the micro-cycle based on the phase type
        micro_config = self._get_micro_cycle_config(phase_type)

        # Create a new coordinator with phase-specific configuration
        micro_coordinator = EDRRCoordinator(
            self.memory_manager,
            self.agent_registry,
            self.workflow_engine
        )

        # Apply phase-specific configuration
        micro_coordinator.max_recursion_depth = micro_config.get("max_recursion_depth", self.max_recursion_depth)

        return micro_coordinator

    def _get_micro_cycle_config(self, phase_type):
        """Get configuration for a specific micro-cycle phase."""
        # Phase-specific configurations
        configs = {
            "expand": {
                "max_recursion_depth": 2,
                "agents": ["divergent_thinker", "context_gatherer"]
            },
            "differentiate": {
                "max_recursion_depth": 2,
                "agents": ["comparative_analyzer", "prioritizer"]
            },
            "refine": {
                "max_recursion_depth": 3,  # More recursion for implementation details
                "agents": ["implementer", "optimizer", "tester"]
            },
            "retrospect": {
                "max_recursion_depth": 1,  # Less recursion for retrospectives
                "agents": ["evaluator", "learner"]
            }
        }

        return configs.get(phase_type, {})

    def transition_to_next_stage(self, current_results):
        """Transition to the next stage in the EDRR."""
        # Check if we should continue or terminate based on results
        if self._should_terminate(current_results):
            return {"status": "early_termination", "context": self.cycle_context}

        # Standard stage transitions
        if self.current_stage == "expand":
            self.current_stage = "differentiate"
            return self.execute_differentiate(current_results)
        elif self.current_stage == "differentiate":
            self.current_stage = "refine"
            return self.execute_refine(current_results)
        elif self.current_stage == "refine":
            self.current_stage = "retrospect"
            return self.execute_retrospect(current_results)
        else:
            return {"status": "completed", "context": self.cycle_context}

    def _should_terminate(self, results):
        """Determine if the EDRR should terminate early."""
        # Check quality thresholds
        if results.get("quality_score", 0) >= results.get("quality_threshold", 1.0):
            return True

        # Check cost-benefit analysis
        if results.get("benefit_score", 1.0) <= results.get("cost_score", 0):
            return True

        # Check for human override
        if results.get("human_terminate", False):
            return True

        return False
```

### 5.2 Stage-Specific Prompts

Each EDRR stage uses specialized prompts to guide agent behavior:

- **Expand Prompts**: Focus on divergent thinking and comprehensive exploration
- **Differentiate Prompts**: Emphasize analytical comparison and evaluation
- **Refine Prompts**: Guide iterative improvement and optimization
- **Retrospect Prompts**: Structure reflection and learning capture


### 5.3 Metrics and Evaluation

The EDRR tracks performance metrics:

- **Diversity Score**: Measures the variety of approaches in Expand stage
- **Decision Quality**: Evaluates the effectiveness of Differentiate stage
- **Improvement Delta**: Quantifies enhancements during Refine stage
- **Learning Efficiency**: Assesses knowledge capture in Retrospect stage


## 6. Configuration Options

The EDRR behavior can be customized through configuration:

- **Stage Weights**: Adjust emphasis on different stages
- **Iteration Limits**: Set maximum iterations for refinement
- **Quality Thresholds**: Define acceptance criteria for outputs
- **Human Intervention Points**: Configure when human input is requested

## Complexity Analysis

The EDRR cycle performs four stages per iteration. If each stage spawns a micro
cycle and recursion continues to depth \(d\), the worst-case time complexity is
\(O(4^d)\). The termination heuristics described in
[Delimiting Recursion Algorithms](delimiting_recursion_algorithms.md) bound \(d\)
and keep execution practical. Unit tests such as
`tests/unit/application/edrr/test_coordinator.py` and behavior tests like
`tests/behavior/features/general/edrr_cycle.feature` verify stage transitions and
early termination.

## 7. Future Enhancements

Planned improvements to the EDRR implementation:

- **Adaptive Stage Sequencing**: Dynamically adjust the process based on task characteristics
- **Parallel Sub-cycles**: Allow nested EDRR cycles for complex problems
- **Cross-project Learning**: Apply insights from previous projects to new contexts
- **Customizable Stage Templates**: Enable domain-specific EDRR variations


## 8. Conclusion

The EDRR provides a structured framework for iterative development in DevSynth, enabling systematic exploration, evaluation, improvement, and learning. By integrating with the WSDE model and hybrid memory system, it supports collaborative, knowledge-driven software development.
## Implementation Status

This feature is **implemented**. Core functionality resides in `src/devsynth/application/edrr/coordinator/core.py` and `edrr_coordinator_enhanced.py`.

## What proofs confirm the solution?
- BDD scenarios in [`tests/behavior/features/edrr_cycle_specification.feature`](../../tests/behavior/features/edrr_cycle_specification.feature) ensure termination and expected outcomes.
- Finite state transitions and bounded loops guarantee termination.

## References

- [DeepAgents Library](https://github.com/langchain-ai/deepagents)
- [DeepAgents Documentation](https://docs.langchain.com/oss/python/deepagents/overview)
- [Cormen, T. H., C. E. Leiserson, R. L. Rivest, and C. Stein. Introduction to Algorithms. 4th ed., MIT Press, 2022.](https://mitpress.mit.edu/9780262033848/introduction-to-algorithms/)
