---
title: "Agent Adapter Example"
date: "2025-07-01"
version: "1.0.0"
tags:
  - "getting-started"
  - "agent-adapter"
  - "example"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-07-01"
---

# Agent Adapter Example

This guide demonstrates how to combine the DevSynth CLI with direct use of the
`AgentAdapter` Python API. The accompanying script lives in
[`examples/agent_adapter/adapter_example.py`](../../examples/agent_adapter/adapter_example.py).

## 1. Initialize a Project

Create a new project directory and initialize DevSynth:

```bash
# Create a project named agent-demo
devsynth init --path agent-demo
cd agent-demo
```

## 2. Invoke the CLI

Generate the standard artifacts using the CLI:

```bash
# Assuming you added requirements.md
devsynth spec --requirements-file requirements.md
devsynth test
devsynth code
```

## 3. Use the AgentAdapter

Run the example script to create an agent, add it to a team, and process a task:

```bash
python ../examples/agent_adapter/adapter_example.py
```

The script performs the following steps:

```python
from devsynth.adapters.agents.agent_adapter import AgentAdapter

adapter = AgentAdapter()
adapter.create_team("demo")
adapter.set_current_team("demo")

agent = adapter.create_agent("orchestrator")
adapter.add_agent_to_team(agent)

result = adapter.process_task({
    "task_type": "specification",
    "requirements": "Build a CLI todo app"
})
print(result)
```

This demonstrates programmatic use of the agent system alongside the CLI
workflow.
