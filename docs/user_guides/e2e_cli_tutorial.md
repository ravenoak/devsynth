---

title: "End-to-End CLI Tutorial"
date: "2025-07-15"
version: "0.1.0a1"
tags:
  - user-guide
  - tutorial
status: published
author: DevSynth Team
last_reviewed: "2025-07-15"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">User Guides</a> &gt; End-to-End CLI Tutorial
</div>

# End-to-End CLI Tutorial

This tutorial walks through a full DevSynth workflow using the command line. It uses the [e2e_cli_example](../../examples/e2e_cli_example) project as a reference.

## 1. Initialize the Project

```bash
devsynth init --path examples/e2e_cli_example
```

## 2. Add Requirements

Edit `examples/e2e_cli_example/requirements.md` with your desired features.

## 3. Generate Specs and Tests

```bash
devsynth spec --requirements-file examples/e2e_cli_example/requirements.md
devsynth test
```

## 4. Generate Code

```bash
devsynth code
```

## 5. Run the Pipeline

```bash
devsynth run-pipeline
```

Review the generated code in `examples/e2e_cli_example/src` and tests in `examples/e2e_cli_example/tests`.
