---
title: "UXBridge Interaction Flow"
date: "2025-06-16"
version: "1.0.0"
tags:
  - "implementation"
  - "pseudocode"
  - "uxbridge"
status: "draft"
author: "DevSynth Team"
last_reviewed: "2025-06-16"
---

# UXBridge Interaction Flow

The following pseudocode illustrates how the CLI or WebUI communicate with core workflows through the `UXBridge` abstraction.

```pseudocode
class UXBridge:
    function ask_question(message) -> Response
    function confirm_choice(message) -> bool
    function display_result(message)

function run_workflow():
    task = UXBridge.ask_question("What task should DevSynth run?")
    if UXBridge.confirm_choice("Run " + task + " now?"):
        result = CoreModules.execute(task)
        UXBridge.display_result(result.summary)
```

This flow enables a shared implementation for both the command-line interface in `interface/cli` and the future WebUI.

## Current Limitations

The `UXBridge` abstraction is still conceptual. A concrete interface layer and
end-to-end tests have not yet been created, and WebUI support is incomplete.
