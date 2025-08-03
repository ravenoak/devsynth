---
author: DevSynth Team
date: '2025-07-12'
last_reviewed: '2025-07-12'
status: draft
tags:
- developer-guide
title: Agent Tools
version: 0.1.0
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Agent Tools
</div>

# Agent Tools Security Model

Agent tools are executed inside a sandbox to minimize the impact of untrusted
code.

## File System Restrictions

Tools may only read and write within the DevSynth project directory. Attempts to
access paths outside the repository raise a ``PermissionError``.

## Shell Command Restrictions

Shell commands are blocked by default. A tool can opt into shell access during
registration by setting ``allow_shell=True``. Without this flag any use of
``subprocess.run`` or ``subprocess.Popen`` raises ``PermissionError``.

## Usage

```python
from devsynth.agents.tools import tool_registry


def my_tool():
    ...


tool_registry.register(
    "example",
    my_tool,
    description="Example tool",
    parameters={},
    allow_shell=False,
)
```

This model ensures tools operate with least privilege while still supporting
explicitly authorized commands.
