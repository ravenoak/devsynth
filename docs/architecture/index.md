---
author: DevSynth Team
date: '2025-06-16'
last_reviewed: "2025-10-21"
status: published
tags:
- architecture
- design
- system
title: DevSynth Architecture
version: "0.1.0-alpha.1"
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Architecture</a> &gt; DevSynth Architecture
</div>

# DevSynth Architecture

This section provides detailed information about the architecture of DevSynth, including its components, design patterns, and frameworks.

## Core Architecture Documents

- **[Overview](overview.md)**: A high-level overview of the DevSynth architecture.
- **[Hexagonal Architecture](hexagonal_architecture.md)**: Details on the hexagonal (Hexagonal Architecture) architecture used in DevSynth.
- **[Init Workflow](init_workflow.md)**: Sequence diagram for the interactive initialization process.
- **[UXBridge](uxbridge.md)**: How CLI modules are decoupled from the UI and reused by the future WebUI.
- **[Phase 1 Overhaul](phase1_overhaul.md)**: Summary of the CLI refactor, unified configuration, and UXBridge pattern.
- **[WebUI Overview](webui_overview.md)**: Layout of the NiceGUI interface and its use of UXBridge.
- **[CLI and Textual UXBridge Integration](cli_textual_uxbridge.md)**: Flowchart describing how prompt-toolkit and Textual bridges reuse shared workflows.

## System Components

- **[Agent System](agent_system.md)**: Information about the agent-based system architecture.
- **[Memory System](memory_system.md)**: Documentation on the memory system used for storing and retrieving information.
- **[Documentation Ingestion](documentation_ingestion.md)**: Offline ingestion of local project documentation.
- **[Provider System](provider_system.md)**: Details on the provider system for integrating external services.

## Methodologies and Frameworks

- **[Dialectical Reasoning](dialectical_reasoning.md)**: Information about the dialectical reasoning approach used in DevSynth.
- **[EDRR Framework](edrr_framework.md)**: Documentation on the EDRR framework.
- **[Recursive EDRR Architecture](recursive_edrr_architecture.md)**: Details on nesting EDRR cycles and termination logic.
- **[WSDE Agent Model](wsde_agent_model.md)**: Details on the Wide Sweep, Deep Exploration agent model.

## Overview

The Architecture section provides a comprehensive view of DevSynth's design and structure. It explains how the different components of the system work together to achieve the project's goals.

DevSynth follows a hexagonal architecture (also known as Hexagonal Architecture) that separates the core domain logic from external adapters and application services. This architecture enables flexibility, testability, and maintainability by ensuring that the core business logic is isolated from external concerns.

The system is composed of several key components:

- **Agent System**: A collection of specialized agents that work together to perform various tasks in the development process.
- **Memory System**: A sophisticated system for storing and retrieving information, enabling agents to maintain context and learn from past interactions.
- **Provider System**: A flexible integration layer that allows DevSynth to work with different LLM providers and external services.

DevSynth also employs several methodologies and frameworks:

- **Dialectical Reasoning**: A structured approach to problem-solving that involves thesis, antithesis, and synthesis.
- **EDRR Framework**: A methodology for expanding, differentiating, refining, and retrospecting on ideas and solutions.
- **WSDE Agent Model**: A model for agent behavior that combines wide exploration with deep analysis.

## Getting Started

If you're new to DevSynth's architecture, we recommend starting with the [Overview](overview.md), which provides a high-level understanding of the system. Then, explore the [Hexagonal Architecture](hexagonal_architecture.md) document to understand the fundamental design pattern used throughout the project.

## Related Documents

- [Developer Guides](../developer_guides/index.md) - Information for developers contributing to DevSynth
- [Technical Reference](../technical_reference/index.md) - Technical reference documentation
- [Specifications](../specifications/index.md) - Detailed specifications for DevSynth components
- [CLI Overhaul Pseudocode](../specifications/cli_overhaul_pseudocode.md) - Design reference for the updated initialization command
- [WebUI Reference](../user_guides/webui_reference.md) - How to use the NiceGUI interface
- [Agent API Reference](../user_guides/api_reference.md) - Programmatic endpoints for automating DevSynth

## Diagrams

Note: Diagrams were last refreshed on 2025-10-02. See scripts/regenerate_architecture_diagrams.py for the automated regeneration path.

- [DPG Overview](diagrams/dpg_overview.svg)
- [Init Workflow (1)](diagrams/init_workflow-1.svg)
- [Init Workflow (2)](diagrams/init_workflow-2.svg)
- [WebUI Overview (1)](diagrams/webui_overview-1.svg)
- [WebUI Overview (2)](diagrams/webui_overview-2.svg)
- [WebUI Overview (3)](diagrams/webui_overview-3.svg)
- [WebUI Overview (4)](diagrams/webui_overview-4.svg)
- [WebUI Overview (5)](diagrams/webui_overview-5.svg)
- [WSDE/EDRR Integration](diagrams/wsde_edrr_integration-1.svg)
- [MCP → A2A → SPARQL Flows](diagrams/mcp_a2a_sparql.md)

## Implementation Status

.
