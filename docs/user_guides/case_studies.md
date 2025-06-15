---
title: "DevSynth Case Studies"
date: "2025-06-14"
version: "1.0.0"
tags:
  - "case study"
  - "examples"
status: "draft"
author: "DevSynth Team"
last_reviewed: "2025-06-14"
---

# DevSynth Case Studies

This document summarizes real-world usage examples of DevSynth. Each case study highlights key takeaways and provides guidance for users following similar workflows.

## Full Workflow Example

The `examples/full_workflow` project demonstrates the complete DevSynth process:

1. **Initialization** – `devsynth init --path .` generated `.devsynth/project.yaml`.
2. **Specification and Test Generation** – `devsynth spec` and `devsynth test` produced `specs.md` and tests under `tests/`.
3. **Code Generation** – `devsynth code` created the implementation in `src/`.
4. **Running and Testing** – after installing dependencies (including `langgraph`), `python src/main.py README.md` produced line, word, and character counts. All unit tests pass with `pytest`.

### Lessons Learned

- Ensure optional dependencies such as `langgraph` are installed when running examples that rely on the adaptive workflow.
- When packaging code in `examples/`, update test modules to adjust `sys.path` so that imports resolve correctly when running `pytest` from the repository root.
 - The command `python src/main.py <file>` runs the word counter. Using `devsynth run-pipeline` executes the configured entrypoint but requires all dependencies to be available.

Future examples should include clear instructions about required extras and test execution so users can reproduce the workflow without issues.
