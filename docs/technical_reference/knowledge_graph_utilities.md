---

author: DevSynth Team
date: '2025-07-07'
last_reviewed: "2025-07-10"
status: published
tags:

- technical-reference

title: Knowledge Graph Utilities in DevSynth
version: "0.1.0-alpha.1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Technical Reference</a> &gt; Knowledge Graph Utilities in DevSynth
</div>

# Knowledge Graph Utilities in DevSynth

This document provides an overview of the knowledge graph utilities in DevSynth and how to use them with the WSDE model for dialectical reasoning.

## Overview

DevSynth includes a set of knowledge graph utilities that allow agents to query and use knowledge stored in a graph-based format. These utilities are particularly useful for enhancing dialectical reasoning by providing access to structured knowledge that can inform critiques, improvements, and evaluations.

**Implementation Status:** Basic querying utilities are available, but advanced reasoning over graph relationships is still experimental.

The knowledge graph utilities are implemented in the `WSDEMemoryIntegration` class and can be used with the `WSDETeam` class for dialectical reasoning.

## Knowledge Graph Utilities

The `WSDEMemoryIntegration` class provides the following utility functions for working with the knowledge graph:

### 1. `query_knowledge_graph`

This is the base method for querying the knowledge graph. It executes a query against the knowledge graph and returns the results.

```python
def query_knowledge_graph(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Query the knowledge graph for information.

    Args:
        query: The query to execute (can be a SPARQL query or a natural language query)
        limit: Maximum number of results to return

    Returns:
        A list of results from the knowledge graph

    Raises:
        ValueError: If the knowledge graph is not available
    """
```

### 2. `query_related_concepts`

This method queries the knowledge graph for concepts related to a given concept.

```python
def query_related_concepts(self, concept: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Query the knowledge graph for concepts related to a given concept.

    Args:
        concept: The concept to find related concepts for
        limit: Maximum number of results to return

    Returns:
        A list of related concepts with their relationships

    Raises:
        ValueError: If the knowledge graph is not available
    """
```

### 3. `query_concept_relationships`

This method queries the knowledge graph for relationships between two concepts.

```python
def query_concept_relationships(self, concept1: str, concept2: str) -> List[Dict[str, Any]]:
    """
    Query the knowledge graph for relationships between two concepts.

    Args:
        concept1: The first concept
        concept2: The second concept

    Returns:
        A list of relationships between the concepts

    Raises:
        ValueError: If the knowledge graph is not available
    """
```

### 4. `query_by_concept_type`

This method queries the knowledge graph for concepts of a specific type.

```python
def query_by_concept_type(self, concept_type: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Query the knowledge graph for concepts of a specific type.

    Args:
        concept_type: The type of concepts to find
        limit: Maximum number of results to return

    Returns:
        A list of concepts of the specified type with their properties

    Raises:
        ValueError: If the knowledge graph is not available
    """
```

### 5. `query_knowledge_for_task`

This method queries the knowledge graph for knowledge relevant to a specific task.

```python
def query_knowledge_for_task(self, task: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
    """
    Query the knowledge graph for knowledge relevant to a specific task.

    Args:
        task: The task to find relevant knowledge for
        limit: Maximum number of results to return

    Returns:
        A list of relevant concepts with their relevance scores

    Raises:
        ValueError: If the knowledge graph is not available
    """
```

## Using Knowledge Graph Utilities with WSDE for Dialectical Reasoning

The `WSDETeam` class provides a method for applying dialectical reasoning with knowledge graph integration:

```python
def apply_dialectical_reasoning_with_knowledge_graph(self, task: Dict[str, Any], critic_agent: Any, wsde_memory_integration: Any) -> Dict[str, Any]:
    """
    Apply dialectical reasoning with knowledge graph integration.

    This implements a knowledge graph-enhanced dialectical review process where:
    1. Relevant knowledge is queried from the knowledge graph for the task
    2. A thesis (initial solution) is identified and analyzed
    3. An antithesis (critique) is developed with reference to knowledge graph concepts
    4. A synthesis (improved solution) is created that incorporates knowledge graph insights
    5. A final evaluation assesses alignment with knowledge graph best practices


    Args:
        task: The task for which dialectical reasoning is being applied
        critic_agent: The agent responsible for applying dialectical reasoning
        wsde_memory_integration: The WSDEMemoryIntegration instance for accessing the knowledge graph

    Returns:
        A dictionary containing the thesis, antithesis, synthesis, evaluation, and knowledge graph insights
    """
```

## Example Usage

Here's an example of how to use the knowledge graph utilities with the WSDE model for dialectical reasoning:

```python
from devsynth.domain.models.WSDE import WSDETeam
from devsynth.application.agents.wsde_memory_integration import WSDEMemoryIntegration
from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter

# Create a WSDE team

team = WSDETeam()

# Add agents to the team

team.add_agent(agent1)
team.add_agent(agent2)

# Create a memory adapter with a knowledge graph-capable backend

memory_adapter = MemorySystemAdapter.create("RDFLib")

# Create a WSDE memory integration

wsde_memory = WSDEMemoryIntegration(memory_adapter, team)

# Create a task

task = {
    "id": "task1",
    "type": "code_generation",
    "description": "Implement a secure authentication system",
    "requirements": ["user authentication", "password security"]
}

# Add a solution to the team

solution = {
    "id": "solution1",
    "agent": "agent1",
    "content": "def authenticate(username, password):\n    return username == 'admin' and password == 'password'",
    "description": "Simple authentication function"
}
team.add_solution(task, solution)

# Apply dialectical reasoning with knowledge graph integration

result = team.apply_dialectical_reasoning_with_knowledge_graph(task, critic_agent, wsde_memory)

# Access the results

thesis = result["thesis"]
antithesis = result["antithesis"]
synthesis = result["synthesis"]
evaluation = result["evaluation"]
knowledge_graph_insights = result["knowledge_graph_insights"]

# Use the knowledge graph utilities directly

related_concepts = wsde_memory.query_related_concepts("authentication")
concept_relationships = wsde_memory.query_concept_relationships("authentication", "security")
security_concepts = wsde_memory.query_by_concept_type("security_concept")
task_relevant_knowledge = wsde_memory.query_knowledge_for_task(task)
```

## Additional WSDETeam Methods

Recent updates introduced more ways to integrate external knowledge when using
`WSDETeam` for dialectical reasoning.

### `apply_enhanced_dialectical_reasoning_with_knowledge`

```python
def apply_enhanced_dialectical_reasoning_with_knowledge(
    self,
    task: Dict[str, Any],
    critic_agent: Any,
    external_knowledge: Dict[str, Any],
) -> Dict[str, Any]:
    """Apply enhanced dialectical reasoning using external knowledge."""
```

This method aligns critiques and improvements with industry standards or other
reference materials supplied via `external_knowledge`.

### `apply_multi_disciplinary_dialectical_reasoning`

```python
def apply_multi_disciplinary_dialectical_reasoning(
    self,
    task: Dict[str, Any],
    critic_agent: Any,
    disciplinary_knowledge: Dict[str, Any],
    disciplinary_agents: List[Any],
) -> Dict[str, Any]:
    """Apply dialectical reasoning with perspectives from multiple disciplines."""
```

Each disciplinary agent provides a perspective on the thesis. The results are
combined to produce a synthesis that balances the concerns of different fields.

## Benefits of Using Knowledge Graph Utilities

Using knowledge graph utilities with the WSDE model for dialectical reasoning provides several benefits:

1. **Enhanced Critiques**: The knowledge graph provides structured information that can be used to generate more informed and comprehensive critiques.

2. **Knowledge-Driven Improvements**: The synthesis phase can incorporate best practices and domain knowledge from the knowledge graph to create better solutions.

3. **Objective Evaluation**: The evaluation phase can assess solutions against established standards and best practices stored in the knowledge graph.

4. **Contextual Reasoning**: The knowledge graph provides context for reasoning about solutions, helping agents understand the broader implications of their decisions.

5. **Consistent Knowledge Access**: All agents in the team can access the same knowledge, ensuring consistency in reasoning and decision-making.


## Current Limitations

- Graph querying functions are minimal and lack performance optimizations.
- More complex reasoning over graph relationships is still experimental.


## Conclusion

The knowledge graph utilities in DevSynth provide a powerful way to enhance dialectical reasoning with structured knowledge. By integrating these utilities with the WSDE model, agents can generate more informed critiques, create better solutions, and provide more objective evaluations.
