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
    function prompt(message) -> Response
    function confirm(message) -> bool
    function print(message)

function run_workflow():
    task = UXBridge.prompt("What task should DevSynth run?")
    if UXBridge.confirm("Run " + task + " now?"):
        result = CoreModules.execute(task)
        UXBridge.print(result.summary)
```

This flow enables a shared implementation for both the command-line interface in `interface/cli` and the future WebUI.
