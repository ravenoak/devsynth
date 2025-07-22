---
author: DevSynth Team
date: '2025-07-08'
last_reviewed: "2025-07-10"
status: published
tags:
- documentation
- glossary
- terminology
- reference
title: DevSynth Glossary of Terms
version: 0.1.0
---

# DevSynth Glossary of Terms

This glossary provides definitions for key terms used throughout the DevSynth project documentation. It ensures consistent terminology and understanding across all documentation artifacts.

## A

### Adapter

In the context of hexagonal architecture, an adapter is a component that connects the application to external systems or interfaces. DevSynth uses adapters for CLI, LLM providers, memory stores, and other external integrations.

### Agent

An autonomous software entity powered by LLMs that performs specific tasks within the DevSynth system. Agents can collaborate, reason, and make decisions based on their assigned roles and responsibilities.

## C

### ChromaDB

A vector database used in DevSynth's memory system for storing and retrieving embeddings. ChromaDB enables semantic search capabilities and is available with an embedded backend. Full external-server support is experimental and may require additional setup.

## D

### Dialectical Reasoning

A method of examining ideas by juxtaposing opposing arguments (thesis and antithesis) to arrive at a resolution (synthesis). DevSynth uses dialectical reasoning for requirements evaluation, code review, and multi-agent collaboration.

## E

### EDRR (Expand, Differentiate, Refine, Retrospect)

A four-phase framework used by DevSynth for project ingestion and adaptation:

- **Expand**: Brainstorming approaches, retrieving relevant documentation, analyzing file structure
- **Differentiate**: Evaluating and comparing approaches, analyzing code quality
- **Refine**: Implementing selected approaches, applying code transformations
- **Retrospect**: Evaluating implementations, verifying code quality, generating final reports


### Embedding

A numerical representation of text that captures its semantic meaning. DevSynth uses embeddings for semantic search and similarity comparison in the memory system.

## H

### Hexagonal Architecture

Also known as Ports and Adapters architecture, it's a design pattern that separates core business logic from external systems. DevSynth uses hexagonal architecture with domain, application, ports, and adapters layers.

## K

### Kuzu

A lightweight graph database used as DevSynth's primary persistent memory backend.

## M

### Memory Adapter

A component that implements the MemoryStore interface to provide specific storage capabilities. DevSynth includes adapters for Kuzu, TinyDB, RDFLib, JSON, and in-memory storage.

### Memory System

The subsystem responsible for storing, retrieving, and managing information in DevSynth. It supports multiple backends and provides a unified interface for semantic search and structured data storage.

### `.devsynth/project.yaml`

A YAML file (`.devsynth/project.yaml`) that defines a project's structure, components, and configuration. It's used by DevSynth to understand and adapt to diverse project structures. Previously known as `manifest.yaml` and sometimes referred to as `devsynth.yaml` in older documentation.

## P

### Port

In the context of hexagonal architecture, a port is an interface that defines how the application interacts with external systems. DevSynth uses ports to define interfaces for memory, LLM providers, and other external systems.

### Provider

A component that provides access to an external service, particularly LLM services like OpenAI or LM Studio. The provider system in DevSynth abstracts away the details of specific LLM implementations.

## R

### RDFLib

A Python library for working with Resource Description Framework (RDF) data. DevSynth uses RDFLib for knowledge graph storage and SPARQL query capabilities.

## T

### TinyDB

A lightweight, document-oriented database for Python. DevSynth uses TinyDB for structured data storage and episodic memory.

## W

### WSDE (Worker Self-Directed Enterprise)

A multi-agent collaboration framework in DevSynth that includes role management, dialectical reasoning, consensus building, and knowledge integration. Key roles include:

- **Primus**: The lead agent that coordinates the team
- **Worker**: Performs implementation tasks
- **Supervisor**: Reviews and evaluates work
- **Designer**: Creates architectural and design solutions
- **Evaluator**: Tests and validates implementations


---

This glossary will be updated as new terms are introduced or existing terms are refined. If you encounter a term that's not defined here, please submit a request for its addition.
## Implementation Status

This glossary is **implemented** and expanded as new terms appear.
