---
title: "Init Workflow"
date: "2025-06-16"
version: "1.0.0"
tags:
  - "architecture"
  - "workflow"
  - "cli"
status: "draft"
author: "DevSynth Team"
last_reviewed: "2025-06-16"
---

# Init Workflow Sequence

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

Both the CLI and the future WebUI will use this same sequence by invoking the
`CoreModules` through the `UXBridge`. This keeps initialization logic in one
place while supporting multiple user interfaces.
