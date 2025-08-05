---
title: "DevSynth Glossary"
date: "2025-08-02"
version: "0.1.0-alpha.1"
tags:
  - "glossary"
  - "terminology"
  - "definitions"
  - "reference"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-02"
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; DevSynth Glossary
</div>

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; DevSynth Glossary
</div>

# DevSynth Glossary

This glossary provides definitions for domain-specific terminology used throughout the DevSynth project documentation. It serves as a reference for both users and developers to ensure consistent understanding of key concepts.

## A

### Adaptive Project Ingestion
The process by which DevSynth dynamically understands and adapts to diverse project structures (including monorepos, multi-language projects, and custom layouts) using a `.devsynth/project.yaml` file and the EDRR framework.

### Agent
An autonomous software component that performs specific tasks within the DevSynth system, such as code generation, analysis, or requirement refinement.

### Agent System
The collection of modular agents and their orchestration framework within DevSynth, powered by LangGraph.

### AgentAdapter
A component that provides a direct interface for interacting with DevSynth's agent capabilities from Python code.

## B

### Behavior-Driven Development (BDD)
A software development methodology that focuses on defining the behavior of a system from the user's perspective using Gherkin syntax (Given/When/Then).

### Breadcrumb Navigation
A navigation aid that shows the hierarchical path to the current document, helping users understand their location within the documentation structure.

## C

### ChromaDB
A vector database used by DevSynth for semantic search and scalable artifact storage.

### CLI (Command Line Interface)
The primary interface for interacting with DevSynth through terminal commands.

### Code Analysis
The process of examining code to understand its structure, dependencies, complexity, and potential issues, implemented in DevSynth using NetworkX.

## D

### Dialectical Reasoning
A method of reasoning that examines opposing ideas (thesis and antithesis) to arrive at a synthesis that resolves contradictions. Used in DevSynth for analyzing and improving solutions.

### Documentation Harmony
The principle that all code, tests, and documents should be kept in sync, with traceability via the Requirements Traceability Matrix.

## E

### EDRR (Expand, Differentiate, Refine, Retrospect)
A framework used by DevSynth for project ingestion and adaptation, consisting of four phases:
- **Expand**: Gather broad information about the project
- **Differentiate**: Identify unique aspects and patterns
- **Refine**: Develop a detailed understanding of specific components
- **Retrospect**: Review and improve the understanding based on new information

### EDRRCoordinator
The component that orchestrates the EDRR process across all system components.

## H

### Hexagonal Architecture
An architectural pattern used in DevSynth that separates core logic from external concerns through ports and adapters, enhancing testability and extensibility.

## J

### JSONFileStore
A simple file-based storage adapter used in DevSynth for legacy and lightweight use cases.

## K

### Kuzu
A graph database used as one of the optional vector store backends in DevSynth.

## L

### LangGraph
A framework for orchestrating workflows with LLMs, used in DevSynth to coordinate agent activities.

### LLM (Large Language Model)
A type of AI model that can understand and generate human language, used in DevSynth for code generation, analysis, and other tasks.

### LM Studio
A tool for running local LLM models, supported as a provider in DevSynth.

## M

### MemoryPort
A unified interface in DevSynth for memory operations, supporting multiple backends such as ChromaDB, TinyDB, and JSON.

### MVUU (Minimum Viable Utility Units)
The smallest useful unit of work recorded by DevSynth for traceability and progress reporting.

## N

### NetworkX
A Python library used in DevSynth for dependency graphing, complexity metrics, and refactoring suggestions.

## O

### Offline Mode
A DevSynth operating mode that functions without network access, using either deterministic text generation or local models.

### OfflineProvider
The LLM provider used when DevSynth is in offline mode, generating deterministic text and embeddings or loading a local model.

## P

### Provider System
The abstraction layer in DevSynth that manages interactions with different LLM providers (OpenAI, LM Studio, etc.) with fallback and selection logic.

### Property-Based Testing
A testing approach that verifies properties of functions across a range of inputs, implemented in DevSynth using the Hypothesis library.

## R

### Requirements Traceability Matrix
A document that maps requirements to design, code, and tests for bidirectional traceability in DevSynth.

## S

### SDLC (Software Development Life Cycle)
The process of planning, creating, testing, and deploying software, which DevSynth aims to automate and enhance.

### Semantic Versioning+
DevSynth's versioning policy, based on Semantic Versioning with additional rules specific to the project.

## T

### TinyDBMemoryAdapter
A structured data storage adapter in DevSynth for project metadata, relationships, and the project structure model.

## U

### UXBridge
A shared interface in DevSynth for CLI, WebUI, and Agent API interactions, providing methods like `ask_question`, `confirm_choice`, and `display_result`.

## V

### Vector Store
A database optimized for storing and retrieving vector embeddings, used in DevSynth for semantic search capabilities.

## W

### WebUI
A graphical user interface for DevSynth based on Streamlit, providing an alternative to the CLI.

### WSDE (Worker Self-Directed Enterprise) Model
A sophisticated multi-agent collaboration framework in DevSynth with role management, dialectical reasoning, consensus building, and knowledge integration capabilities.

---

_Last updated: August 2, 2025_
