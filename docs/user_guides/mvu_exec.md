---
title: "MVU Command Execution"
date: "2025-08-20"
version: "0.1.0a1"
tags:
  - "mvuu"
  - "cli"
status: "draft"
author: "DevSynth Team"
last_reviewed: "2025-08-20"
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">User Guides</a> &gt; MVU Command Execution
</div>

# MVU Command Execution

Use `devsynth mvu exec` to run arbitrary shell commands within the MVU workflow. The command's `stdout` and `stderr` are combined and displayed, and the CLI exits with the underlying command's return code.

```bash
devsynth mvu exec echo hello
```

The above command prints `hello` and exits with code `0`. Errors from the executed command propagate their non-zero exit codes and error messages.

## References

- [Specification: MVU Command Execution](../specifications/mvu-command-execution.md)
- [BDD Feature: MVU shell command execution](../../tests/behavior/features/mvu/command_execution.feature)
