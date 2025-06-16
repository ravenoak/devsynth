---
title: "CLI Overhaul Pseudocode"
date: "2025-06-16"
version: "0.1.0"
tags:
  - "specification"
  - "cli"
  - "pseudocode"
status: "draft"
author: "DevSynth Team"
last_reviewed: "2025-06-16"
---

# Refactored `init` Command

```pseudocode
function init_command():
    config = UnifiedConfigLoader.load()
    if config.exists():
        UXBridge.notify("Project already initialized")
        return
    root = UXBridge.prompt("Project root directory?")
    language = UXBridge.prompt("Primary language?")
    goals = UXBridge.prompt("Project goals?")
    config.set_root(root)
    config.set_language(language)
    config.set_goals(goals)
    config.save()
    UXBridge.notify("Initialization complete")
```

# Unified Configuration Loader

```pseudocode
class UnifiedConfigLoader:
    static function load(path = default_location) -> Config:
        if file_exists(path):
            return Config.parse_yaml(read_file(path))
        else:
            return Config()
```

# `UXBridge` Abstraction

```pseudocode
class UXBridge:
    function prompt(message) -> Response:
        if running_in_cli:
            return CLI.prompt(message)
        else if running_in_web:
            return WebUI.prompt(message)

    function notify(message):
        if running_in_cli:
            CLI.display(message)
        else if running_in_web:
            WebUI.display(message)
```
