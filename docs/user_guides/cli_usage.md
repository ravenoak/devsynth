---
title: CLI Usage
date: "2025-06-19"
version: "0.1.0a1"
tags:
  - user-guide
  - cli
status: draft
author: "DevSynth Team"
last_reviewed: "2025-06-19"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">User Guides</a> &gt; CLI Usage
</div>

# CLI Usage

The table below outlines the most common DevSynth commands with brief
descriptions and example usage. Invoke ``devsynth <command> --help`` for full
option details.

| Command      | Description                                              | Example                                               |
|--------------|----------------------------------------------------------|-------------------------------------------------------|
| init         | Initialize a new project                                 | `devsynth init`                                       |
| spec         | Generate specifications from requirements                | `devsynth spec`                                       |
| test         | Generate tests from specifications                       | `devsynth test`                                       |
| code         | Generate code from tests                                 | `devsynth code`                                       |
| run-pipeline | Run the generated code or a specific target              | `devsynth run-pipeline --target unit-tests`           |
| config       | View or set configuration options                        | `devsynth config --list-models`                       |
| gather       | Interactively gather project goals, constraints and priority | `devsynth gather`                                 |
| inspect      | Inspect requirements from a file or interactively        | `devsynth inspect --input requirements.txt`           |
| refactor     | Execute a refactor workflow based on the current project state | `devsynth refactor`                              |
| webapp       | Generate a web application with the specified framework  | `devsynth webapp`                                     |
| serve        | Run the DevSynth API server                              | `devsynth serve`                                      |
| dbschema     | Generate a database schema for the specified database type | `devsynth dbschema`                                |
| doctor       | Run diagnostics on the current environment               | `devsynth doctor`                                     |
| check        | Alias for doctor command                                 | `devsynth check --quick`                             |
| edrr-cycle   | Run an EDRR cycle                                        | `devsynth edrr-cycle`                                 |
| webui        | Launch the Streamlit WebUI                               | `devsynth webui`                                      |
| completion   | Generate or install shell completion scripts             | `devsynth completion --install`                      |

Use `devsynth --help` for the full list of available commands and options.
## Implementation Status

This guide reflects the current CLI capabilities.
