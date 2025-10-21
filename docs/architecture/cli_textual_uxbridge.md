---
title: "CLI and Textual UXBridge Integration"
date: "2025-10-21"
version: "0.1.0-alpha.2"
tags:
  - "architecture"
  - "cli"
  - "textual"
  - "uxbridge"
  - "prompt-toolkit"
  - "rich"
status: "draft"
author: "DevSynth Team"
last_reviewed: "2025-10-21"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Architecture</a> &gt; CLI and Textual UXBridge Integration
</div>

# CLI and Textual UXBridge Integration

This diagram and narrative explain how the enhanced CLI, prompt-toolkit adapter, and Textual TUI reuse shared workflows through the `UXBridge` abstraction while delivering richer user experiences.

## Sequence Overview

```mermaid
flowchart LR
    subgraph CLI Layer
        Typer[Typer Command]
        PromptToolkit[PromptToolkitSession]
        RichConsole[Rich Console]
    end

    subgraph Textual Layer
        TextualApp[Textual Application]
        TextualBridge[TextualUXBridge]
    end

    subgraph Core Workflows
        UXBridgeInterface[[UXBridge Protocol]]
        Wizards[Setup & Requirements Wizards]
        Services[Application Services]
    end

    Typer -->|invokes| PromptToolkit
    Typer -->|fallback prompts| RichConsole
    TextualApp --> TextualBridge

    PromptToolkit -->|implements| UXBridgeInterface
    TextualBridge -->|implements| UXBridgeInterface
    RichConsole -->|baseline implementation| UXBridgeInterface

    UXBridgeInterface --> Wizards --> Services
    Wizards -->|updates| UXBridgeInterface

    subgraph Observability
        Logs[Sanitised Logs]
        Telemetry[Progress Events]
    end

    UXBridgeInterface --> Logs
    UXBridgeInterface --> Telemetry
```

## Key Points

1. **Capability Negotiation** – `PromptToolkitSession` and `TextualUXBridge` advertise capabilities (`supports_multi_select`, `supports_layout_panels`) so wizards can tailor prompts without branching logic.
2. **Shared Workflows** – Setup and requirements wizards remain unaware of presentation details, calling only the `UXBridge` protocol while receiving navigation events from any bridge.
3. **Observability Alignment** – Structured Rich layouts and Textual panes emit sanitised logs and telemetry events to maintain parity with existing diagnostics.

## Related Documents

- [Specification: CLI UX Enhancements](../specifications/cli-ux-enhancements.md)
- [Specification: Shared UXBridge across CLI, Textual TUI, and WebUI](../specifications/shared-uxbridge-across-cli-and-webui.md)
- [Requirements: FR-90 – FR-93](../system_requirements_specification.md#311-multi-channel-user-experience)
