# DevSynth Cursor IDE Configuration

This directory contains Cursor IDE rules and configuration for effective LLM agent collaboration within the DevSynth project.

## Files Overview

### `rules` - Primary Development Rules
The main rules file containing comprehensive guidance for LLM agents working on DevSynth. This file covers:

- **Mandatory BDD workflow** - Specification-first development requirements
- **Testing discipline** - Speed markers, resource flags, and test organization
- **Command patterns** - Correct usage of Poetry, CLI tools, and task runner
- **File organization** - Where different types of code and documentation belong
- **Quality standards** - Typing, linting, security, and audit compliance
- **Common operations** - Frequent development tasks and their correct execution
- **Error prevention** - Common pitfalls and recovery strategies

## Usage Guidelines

### For LLM Agents
The rules in this directory are designed to enable autonomous operation while maintaining DevSynth's high standards for:
- Code quality and testing discipline
- Security and audit compliance
- Documentation and specification requirements
- Workflow consistency and tool integration

### Integration with Existing Documentation
These Cursor rules complement the existing project documentation for Cursor IDE workflows:
- **CONTRIBUTING.md** - Primary reference for contribution guidelines and setup
- **docs/policies/** - Security, audit, and governance policies  
- **docs/specifications/** - Technical specifications and requirements
- **docs/architecture/** - System architecture and design patterns

**Important:** AGENTS.md and scripts/codex_setup.sh contain Codex-specific instructions and should NOT be referenced for Cursor IDE development.

## Key Principles

### 1. Specification-First Development
All code changes must begin with:
1. Creating a specification in `docs/specifications/`
2. Creating a failing BDD test in `tests/behavior/features/`
3. Only then implementing the solution

### 2. Test Discipline
- Every test must have exactly one speed marker (`fast`, `medium`, `slow`)
- Resource flags control optional service dependencies
- Test organization mirrors source code structure

### 3. Tool Integration
- All Python execution through `poetry run`
- Task runner for common workflows
- Pre-commit hooks for quality assurance
- Dialectical audit for compliance verification

### 4. Quality Standards
- Comprehensive type checking with mypy
- Code formatting with Black and isort
- Security scanning with Bandit and Safety
- Documentation requirements for all changes

## Success Metrics

LLM agents should be able to:
1. Follow the BDD workflow correctly without prompting
2. Maintain test marker discipline automatically
3. Use the correct command patterns consistently
4. Organize files in appropriate directories
5. Meet all quality and security requirements
6. Integrate seamlessly with existing tooling

## Maintenance

These rules should be updated when:
- Development workflows change
- New tools or standards are adopted
- Common LLM agent issues are identified
- Project structure or organization evolves

## Feedback and Improvement

If LLM agents consistently struggle with specific aspects of DevSynth development, consider:
1. Adding more specific guidance to the rules
2. Creating additional examples or command patterns
3. Updating error prevention strategies
4. Enhancing integration with existing tooling

The goal is continuous improvement of agent effectiveness while maintaining DevSynth's rigorous standards for quality and compliance.
