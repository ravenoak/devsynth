---

author: DevSynth Team
date: '2025-07-01'
last_reviewed: "2025-07-10"
status: published
tags:

- getting-started
- agent-adapter
- example

title: Agent Adapter Example
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Getting Started</a> &gt; Agent Adapter Example
</div>

# Agent Adapter Example

This guide demonstrates how to combine the DevSynth CLI with direct use of the
`AgentAdapter` Python API. The accompanying script lives in
[`examples/agent_adapter/adapter_example.py`](../../examples/agent_adapter/adapter_example.py).

## Environment Requirements

Ensure **Python 3.12 or higher** is installed. Poetry is recommended for dependency management during development.

You can perform the following CLI steps via the WebUI as well. Launch it with `devsynth webui` and use the pages that correspond to each command.

## 1. Initialize a Project

Create a new project directory and initialize DevSynth:

```bash

# Create a project named agent-demo

devsynth init --path agent-demo
cd agent-demo
```

The initializer detects existing configuration files and will prompt you interactively when run in an existing project directory.

## 2. Invoke the CLI

Generate the standard artifacts using the CLI:

```bash

# Assuming you added requirements.md

devsynth inspect --requirements-file requirements.md
devsynth run-pipeline
devsynth refactor
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
## Implementation Status

.
