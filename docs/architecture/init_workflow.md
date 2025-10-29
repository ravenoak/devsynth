---
author: DevSynth Team
date: '2025-06-16'
last_reviewed: "2025-07-10"
status: draft
tags:

- architecture
- workflow
- cli

title: Init Workflow
version: "0.1.0a1"
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Architecture</a> &gt; Init Workflow
</div>

# Init Workflow

The redesigned `init` command collects essential project details before creating a configuration file.

```mermaid
sequenceDiagram
    participant U as User
    participant CLI as CLI
    participant UX as UXBridge
    participant Core as CoreModules
    U->>CLI: run `devsynth init`
    CLI->>UX: request setup info
    UX->>U: prompt for project root
    U-->>UX: provide path
    UX->>U: select language(s)
    U-->>UX: choose language(s)
    UX->>U: describe project goals
    U-->>UX: confirm goals
    UX->>Core: initialize project
    Core-->>UX: summary
    UX->>U: display completion
```

![Init Workflow Sequence Diagram](diagrams/init_workflow-1.svg)

Both the CLI and the future WebUI will use this same sequence by invoking the
`CoreModules` through the `UXBridge`. This keeps initialization logic in one
place while supporting multiple user interfaces.

## Requirements Wizard Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant CLI as CLI
    participant UX as UXBridge
    U->>CLI: run `devsynth requirements wizard`
    CLI->>UX: prompt for details
    UX->>U: gather title/description/constraints
    U-->>UX: provide answers
    UX->>CLI: save structured file
```

![Requirements Wizard Sequence Diagram](diagrams/init_workflow-2.svg)

This wizard shares the same prompts across interfaces thanks to the
`UXBridge` abstraction.
## Implementation Status

This workflow is **implemented** and used by both the CLI and WebUI
via the `UXBridge` layer.
