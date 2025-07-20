---
author: DevSynth Team
date: '2025-06-16'
last_reviewed: "2025-07-10"
status: draft
tags:

- implementation
- pseudocode
- uxbridge

title: Interactive Requirements Collection Pseudocode
version: 0.1.0
---

# Interactive Requirements Collection Pseudocode

The CLI and WebUI gather requirements using the concrete `UXBridge` interface and
store results with `TinyDBMemoryAdapter`.

```python
from devsynth.interface.ux_bridge import UXBridge
from devsynth.application.memory.adapters.tinydb_memory_adapter import TinyDBMemoryAdapter
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.memory import MemoryItem, MemoryType

class RequirementsCollector:
    def __init__(self, bridge: UXBridge) -> None:
        self.bridge = bridge
        self.memory = MemoryManager(adapters={"TinyDB": TinyDBMemoryAdapter()})

    def gather(self) -> None:
        name = self.bridge.ask_question("Project name?")
        language = self.bridge.ask_question("Primary language?")
        features = self.bridge.ask_question("Desired features (comma separated)?")
        if self.bridge.confirm_choice("Save these settings?"):
            item = MemoryItem(
                content={"name": name, "language": language, "features": features},
                memory_type=MemoryType.WORKING,
            )
            self.memory.adapters["TinyDB"].store(item)
            self.bridge.display_result("Requirements saved")
        else:
            self.bridge.display_result("Cancelled")
```

This approach keeps prompts consistent across interfaces while persisting answers in TinyDB.

## Current Limitations

The interactive requirements collection flow is not implemented yet. Error
handling, persistent storage of answers, and real-time validation remain future
work.
## Implementation Status

This feature is **planned** and not yet implemented.
