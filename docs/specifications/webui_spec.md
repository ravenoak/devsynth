---
author: DevSynth Team
date: '2025-06-16'
status: draft
tags:
- specification
- webui
- ux
title: WebUI Specification
version: 0.1.0
---

# WebUI Specification

This specification describes the initial graphical interface for
DevSynth. The WebUI is implemented using Streamlit and communicates
with the core workflows through the `UXBridge` abstraction. The goal is
to offer a simple alternative to the CLI while reusing the same
orchestration logic.

## Layout

- **Sidebar Navigation** with the following sections:
  1. **Project Onboarding** – initialize or onboard an existing project.
  2. **Requirements Gathering** – inspect requirements and generate
     specifications.
  3. **Code Analysis** – analyze the project codebase.
  4. **Synthesis Execution** – generate tests, produce code and run the
     pipeline.
  5. **Configuration Editing** – view or update project settings.

Each section appears as a collapsible panel with progress indicators
shown while tasks are running.

## UXBridge Integration

The WebUI calls the same functions used by the CLI, passing itself as
the `UXBridge` implementation. This ensures consistent behaviour across
interfaces and keeps workflow logic in a single location.

## Future Work

- Improve layout and styling.
- Provide real-time log streaming to the browser.
- Support multi-user collaboration.
## Implementation Status

This feature is **in progress** and not yet implemented.
