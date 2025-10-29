---

author: DevSynth Team
date: '2024-06-01'
last_reviewed: "2025-07-10"
status: published
tags:
- developer-guides
- contributing
- development
title: DevSynth Developer Guides
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; DevSynth Developer Guides
</div>

# DevSynth Developer Guides

This section is for developers contributing to the DevSynth project or those looking to understand its internal workings for extension or integration.

## Core Development Guides

- **[Onboarding Guide](onboarding.md)**: A guide for new developers joining the DevSynth project.
- **[Contributing Guide](contributing.md)**: Guidelines for contributing to the DevSynth project, including code style, commit conventions, and the pull request process.
- **[Development Setup](development_setup.md)**: Instructions on how to set up a local development environment for DevSynth.
- **[Deployment Setup](deployment_setup.md)**: Quick guide to running DevSynth with Docker Compose and the optional ChromaDB service.
- **[Code Style](code_style.md)**: Specific code style guidelines and conventions followed in the DevSynth project.
- **[Dependency Management](dependency_management.md)**: How to update and check project dependencies.
- **[Dependency Strategy](dependencies.md)**: Overview of optional extras and CI checks.
- **[Repository Structure](../repo_structure.md)**: An overview of how the DevSynth repository is organized.
- **[Requirements Wizard Structure](requirements_wizard_structure.md)**: Overview of the requirements wizard helpers.
- **[Sprint–EDRR Ceremony Alignment](sprint_edrr_ceremony_alignment.md)**: Map sprint ceremonies to EDRR phases.
- **[Agent Tools](agent_tools.md)**: Overview of the tool registry and how to add new tools.
- **[Code Analysis Guide](code_analysis.md)**: Overview of repository analysis and AST transformation utilities.
- **[Virtual Environment Enforcement](virtual_environment_enforcement.md)**: Ensure all development commands run inside the Poetry-managed virtual environment.

## Testing Guides

- **[Testing Guide](testing.md)**: Detailed information about the testing philosophy, structure, types of tests, and how to run and write tests for DevSynth.
- **[Testing Best Practices](testing_best_practices.md)**: Best practices for writing effective tests for DevSynth.
- **[Test Isolation Best Practices](test_isolation_best_practices.md)**: Guidelines for ensuring tests are properly isolated.
- **[Hermetic Testing](hermetic_testing.md)**: Information about hermetic testing in DevSynth.
- **[Testing Agents](testing_agents.md)**: Guidelines for testing agent-based components.
- **[Test Templates](test_templates.md)**: Templates for creating different types of tests.
- **[TDD/BDD Approach](tdd_bdd_approach.md)**: Information about the Test-Driven Development and Behavior-Driven Development approaches used in DevSynth.
- **[TDD/BDD EDRR Integration](tdd_bdd_edrr_integration.md)**: How TDD/BDD integrates with the EDRR framework.
- **[TDD/BDD EDRR Training](tdd_bdd_edrr_training.md)**: Training materials for TDD/BDD with EDRR.

## Configuration and System Guides

- **[DevSynth Configuration](devsynth_configuration.md)**: Information about configuring DevSynth.
- **[Configuration Storage System](configuration_storage_system.md)**: Details about the configuration storage system.
- **[DevSynth Contexts](devsynth_contexts.md)**: Information about the context system in DevSynth.
- **[Error Handling](error_handling.md)**: Guidelines for error handling in DevSynth.

## Process Guides

- **[Cross-Functional Review Process](cross_functional_review_process.md)**: Information about the cross-functional review process.
- **[Secure Coding](secure_coding.md)**: Guidelines for secure coding practices.
- **[Security Audit Guide](security_audits.md)**: How to run and interpret automated security audits.

## Overview

The Developer Guides section provides comprehensive documentation for developers working on the DevSynth project. Whether you're a new contributor or an experienced developer, these guides will help you understand the project's architecture, coding standards, testing approach, and development processes.

The guides are organized into several categories:

- **Core Development Guides**: Essential information for getting started with development, including setup instructions, contribution guidelines, and code style.
- **Testing Guides**: Detailed information about the testing approach, best practices, and specific testing techniques used in DevSynth.
- **Configuration and System Guides**: Information about configuring DevSynth and understanding its core systems.
- **Process Guides**: Documentation about development processes and practices.

## Getting Started

If you're new to DevSynth development, we recommend starting with the [Onboarding Guide](onboarding.md), followed by the [Development Setup](development_setup.md) guide to set up your environment. Then, review the [Contributing Guide](contributing.md) to understand how to contribute to the project.

## Related Documents

- [Architecture Overview](../architecture/overview.md) - Overview of DevSynth's architecture
- [Technical Reference](../technical_reference/index.md) - Technical reference documentation
- [User Guides](../user_guides/index.md) - Guides for users of DevSynth
## Implementation Status

.
