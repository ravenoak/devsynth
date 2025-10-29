---

title: "Progressive Feature Setup"
date: "2025-06-01"
version: "0.1.0a1"
tags:
  - "setup"
  - "user guide"
  - "dialectical-reasoning"
  - "formal-verification"

status: "published"
author: "DevSynth Team"
last_reviewed: "2025-07-10"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">User Guides</a> &gt; Progressive Feature Setup
</div>

# Progressive Feature Setup

This guide describes how to install DevSynth with minimal features and progressively enable more advanced capabilities such as dialectical reasoning, property-based testing, and SMT-based formal verification.

## Basic Installation

1. Install DevSynth from PyPI using Poetry or pipx:


   ```bash
   poetry add devsynth
   # or for an isolated install
   pipx install devsynth
   ```

   For development from source, clone the repository and run the provisioning script:

   ```bash
   bash scripts/install_dev.sh  # installs go-task and runs poetry install --with dev --all-extras
   task --version && poetry run devsynth --help
   ```

2. Initialize a new project:


   ```bash
   devsynth init --path ./my-project
   cd my-project
   ```

   The initialization command creates a `.devsynth/project.yaml` file with default settings and feature flags disabled.

You may also use the WebUI for these steps by running `devsynth webui` and navigating through the onboarding page.

## Enabling Dialectical Reasoning

1. Edit `.devsynth/project.yaml` or use the CLI to enable the feature:


   ```bash
   devsynth config features.dialectical_reasoning true
   ```

   This sets `features.dialectical_reasoning: true` in the configuration file. See [docs/configuration.md](../configuration.md) for a full description of feature flags.

   For details on how this flag changes agent behavior and how to tune reasoning depth, see [Dialectical Reasoning Flag](../architecture/dialectical_reasoning.md#dialectical-reasoning-flag).

2. Run your workflows as usual. When dialectical reasoning is enabled, agents will perform critique and synthesis steps automatically.


## Enabling Property-Based Tests

1. Activate the `formalVerification.propertyTesting` flag:


   ```bash
   devsynth config formalVerification.propertyTesting true
   ```

   This option adds Hypothesis-based property tests when you run `devsynth run-pipeline`.

2. Execute the test generation command:


   ```bash
   devsynth run-pipeline --property-testing
   ```

   The `--property-testing` switch ensures property-based tests are executed alongside regular unit tests.

## Enabling Formal Proof Tools

1. Turn on SMT checks in your configuration:


   ```bash
   devsynth config formalVerification.smtChecks true
   ```

   This writes `formalVerification.smtChecks: true` to `.devsynth/project.yaml`.

2. Use the proof tools during test runs:


   ```bash
   devsynth run-pipeline --smt-checks
   ```

   The CLI switch engages the optional Z3/PySMT verification steps defined in `config/*.yml`.

## Summary

Start with a minimal installation and gradually enable advanced reasoning and verification features as your project matures. Configuration values live in `.devsynth/project.yaml` and can be toggled via `devsynth config`. CLI switches such as `--property-testing` and `--smt-checks` allow you to control these features when running commands.

## Implementation Status

.
