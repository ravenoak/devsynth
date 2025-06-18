---
title: "Interactive Requirements Collection Pseudocode"
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

# Interactive Requirements Collection

The following pseudocode demonstrates how both the CLI and WebUI gather project requirements through the `UXBridge` abstraction.

```pseudocode
class RequirementsCollector:
    function gather():
        name = UXBridge.ask_question("Project name?")
        language = UXBridge.ask_question("Primary language?")
        features = UXBridge.ask_question("Desired features (comma separated)?")
        if UXBridge.confirm_choice("Save these settings?"):
            Requirements.save(name, language, features)
            UXBridge.display_result("Requirements saved")
        else:
            UXBridge.display_result("Cancelled")
```

This approach ensures identical prompts appear in the CLI and the WebUI without duplicating logic.
