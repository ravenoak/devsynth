---
author: DevSynth Team
date: '2025-07-12'
last_reviewed: '2025-07-12'
status: published
tags:
- developer-guide
title: Agent Tools
version: "0.1.0a1"
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Agent Tools
</div>

# Agent Tools

DevSynth agents rely on a registry of sandboxed tools to extend their
behaviour. This guide describes the tools that ship with DevSynth, how to work
with the registry and the steps for adding new tools.

## Existing Tools

| Name | Description |
|------|-------------|
| `alignment_metrics` | Collects code alignment metrics and optionally writes a report. |
| `run_tests` | Executes the project's pytest suites and returns their output. |
| `security_audit` | Runs static analysis and dependency checks to surface security issues. |
| `doctor` | Validates configuration files and environment setup. |

You can inspect the registry programmatically:

```python
from devsynth.agents.tools import get_tool_registry

registry = get_tool_registry()
for name, meta in registry.list_tools().items():
    print(name, meta["description"])
```

Tool metadata can also be exported in OpenAI's function-call format:

```python
from devsynth.agents.tools import get_openai_tools

openai_tools = get_openai_tools()
```

## Adding a New Tool

1. Implement the tool as a plain function.
2. Register it with ``tool_registry.register``.
3. Describe the parameters using a JSON schema dictionary.
4. Set ``allow_shell=True`` only if the tool must execute shell commands.

```python
from devsynth.agents.tools import tool_registry

def shout(text: str) -> str:
    return text.upper()

tool_registry.register(
    "shout",
    shout,
    description="Example tool",
    parameters={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Text to convert",
            }
        },
        "required": ["text"],
    },
    allow_shell=False,
)
```

## Invoking Tools

```python
from devsynth.agents.tools import get_tool_registry

registry = get_tool_registry()
run_tests = registry.get("run_tests")
result = run_tests(target="unit-tests")
print(result["output"])
```

## Security Model

All tools execute within a sandbox that limits file system access to the
repository and blocks shell commands unless ``allow_shell=True`` is specified.
This design enforces least privilege while still enabling explicitly authorised
commands.
