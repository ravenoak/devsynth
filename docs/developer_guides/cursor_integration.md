---
title: "Cursor IDE Integration Guide"
date: "2025-10-22"
version: "0.1.0a1"
tags:
  - "cursor"
  - "ide"
  - "integration"
  - "edrr"
  - "sdd"
  - "bdd"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-10-22"
---

# Cursor IDE Integration Guide

## Overview

DevSynth seamlessly integrates with Cursor IDE to provide structured AI assistance that aligns with the project's established methodologies. This integration transforms Cursor into a natural extension of DevSynth's agentic development platform, enhancing developer productivity while maintaining quality standards and architectural consistency.

## Integration Benefits

### Enhanced Developer Experience
- **Structured Guidance**: Clear workflows for complex development tasks
- **Quality Assurance**: Built-in compliance with project standards and best practices
- **Context Awareness**: AI assistance that understands project architecture, patterns, and specifications
- **Consistency**: Standardized approaches across all development activities

### Methodology Alignment
- **EDRR Framework**: Structured thinking process integrated into Cursor workflows
- **SDD + BDD**: Intent-driven development with executable specifications
- **Multi-Agent Collaboration**: Enhanced coordination between human and AI agents
- **Continuous Improvement**: Learning integration from retrospective analysis

## Integration Components

### 1. Project Constitution
The project constitution (`constitution.md`) serves as the foundational governance document for all development activities:

```markdown
# DevSynth Project Constitution

## Technology Stack
- **Framework**: DevSynth 0.1.0a1 (Agentic Software Engineering Platform)
- **Architecture**: Hexagonal architecture with ports and adapters
- **Methodology**: EDRR (Expand-Differentiate-Refine-Retrospect) framework

## Development Workflow
1. **Expand**: Generate multiple diverse approaches
2. **Differentiate**: Compare options using multiple criteria
3. **Refine**: Implement with comprehensive testing
4. **Retrospect**: Analyze outcomes and capture learnings
```

### 2. Cursor Rules (`.cursor/rules/`)
Always-apply and auto-attach rules that guide AI behavior:

- **`00-architecture.mdc`**: Project constitution and core principles (always applied)
- **`01-edrr-framework.mdc`**: EDRR phase guidance and structured thinking (always applied)
- **`02-specification-driven.mdc`**: SDD + BDD integration (always applied)
- **`03-testing-philosophy.mdc`**: Testing standards and practices (always applied)
- **`04-security-compliance.mdc`**: Security requirements (always applied)
- **`05-dialectical-reasoning.mdc`**: Dialectical audit policy (always applied)

### 3. Cursor Commands (`.cursor/commands/`)
Structured workflow commands for common development tasks:

- **EDRR Workflow**: `/expand-phase`, `/differentiate-phase`, `/refine-phase`, `/retrospect-phase`
- **Specification Management**: `/generate-specification`, `/validate-bdd-scenarios`
- **Testing**: `/generate-test-suite`
- **Quality Assurance**: `/code-review`

## Development Workflow

### 1. Feature Development with EDRR

#### Step 1: Expand Phase
```bash
/expand-phase user authentication with JWT tokens
```

The AI generates multiple approaches:
- **Approach 1**: FastAPI Security with OAuth2
- **Approach 2**: Custom JWT implementation
- **Approach 3**: Third-party authentication service integration

#### Step 2: Differentiate Phase
```bash
/differentiate-phase authentication approaches with security analysis
```

The AI provides structured comparison:
- **Technical Complexity**: Approach 1 (Low), Approach 2 (Medium), Approach 3 (High)
- **Security Risk**: Approach 1 (Low), Approach 2 (Medium), Approach 3 (Low)
- **Development Time**: Approach 1 (Fast), Approach 2 (Medium), Approach 3 (Slow)

#### Step 3: Refine Phase
```bash
/refine-phase implement FastAPI Security OAuth2 approach
```

The AI implements the selected approach with:
- Core authentication functionality
- Comprehensive test coverage
- Security validation
- Documentation updates

#### Step 4: Retrospect Phase
```bash
/retrospect-phase authentication implementation analysis
```

The AI analyzes outcomes and captures learnings:
- **What Worked Well**: FastAPI Security integration was straightforward
- **Challenges**: OAuth2 configuration required careful setup
- **Improvements**: Create reusable authentication patterns

### 2. Specification-Driven Development

#### Creating Specifications
```bash
/generate-specification user profile management feature
```

The AI creates:
- **Markdown specification** in `docs/specifications/`
- **BDD feature file** in `tests/behavior/features/`
- **Implementation plan** with clear tasks and milestones

#### BDD Scenario Validation
```bash
/validate-bdd-scenarios user_profile_management.feature
```

The AI validates:
- **Syntax compliance**: Gherkin structure and keywords
- **Content quality**: Clarity, completeness, and testability
- **Implementation feasibility**: Technical viability with current architecture

### 3. Comprehensive Testing

#### Test Suite Generation
```bash
/generate-test-suite user_profile_component
```

The AI creates:
- **Unit tests** in `tests/unit/` for individual components
- **Integration tests** in `tests/integration/` for component interactions
- **BDD scenarios** in `tests/behavior/features/` for user behaviors
- **Test coverage analysis** with improvement recommendations

#### Code Review
```bash
/code-review recent_changes_in_user_profile_module
```

The AI performs:
- **Quality assessment**: Code quality, readability, maintainability
- **Architecture compliance**: Alignment with hexagonal architecture
- **Security review**: Security vulnerability identification
- **Performance analysis**: Performance implications and optimizations

## Custom Modes

### EDRRImplementer Mode
**Keybinding**: `Cmd+Shift+E`
**Purpose**: Implementation within EDRR framework with comprehensive testing

**Capabilities**:
- Read specifications and understand requirements
- Implement following established patterns
- Generate comprehensive tests
- Validate against quality gates
- Update documentation

### SpecArchitect Mode
**Keybinding**: `Cmd+Shift+S`
**Purpose**: Specification and BDD scenario creation

**Capabilities**:
- Create SDD specifications with clear requirements
- Write BDD scenarios with proper Gherkin syntax
- Validate specification completeness and clarity
- Ensure traceability between requirements and implementation

### TestArchitect Mode
**Keybinding**: `Cmd+Shift+T`
**Purpose**: Comprehensive test suite creation and validation

**Capabilities**:
- Generate unit, integration, and BDD tests
- Ensure proper speed markers and resource gating
- Validate test coverage and quality
- Create appropriate mocks and fixtures

### CodeReviewer Mode
**Keybinding**: `Cmd+Shift+R`
**Purpose**: Comprehensive code review and quality assessment

**Capabilities**:
- Analyze code quality and architecture compliance
- Identify security vulnerabilities and performance issues
- Suggest improvements and best practice applications
- Validate testing coverage and documentation

### DialecticalThinker Mode
**Keybinding**: `Cmd+Shift+D`
**Purpose**: Apply dialectical reasoning and multi-perspective analysis

**Capabilities**:
- Apply thesis-antithesis-synthesis reasoning
- Consider multiple perspectives (technical, business, security, quality)
- Question assumptions and explore alternatives
- Build consensus through structured analysis

## Best Practices

### 1. Always Start with Intent
- Reference specifications in `docs/specifications/` before implementing
- Use BDD scenarios in `tests/behavior/features/` to define acceptance criteria
- Follow the project constitution for governance and standards

### 2. Follow EDRR Process
- **Expand**: Generate multiple approaches and explore alternatives
- **Differentiate**: Compare options using structured analysis
- **Refine**: Implement with comprehensive testing and quality assurance
- **Retrospect**: Capture learnings and improve future processes

### 3. Maintain Quality
- Use testing commands for comprehensive test coverage
- Apply code review for quality assurance
- Follow security and compliance requirements
- Update documentation as you implement

### 4. Leverage Memory System
- Use the hybrid memory system for context and learning
- Reference similar implementations and patterns
- Apply learnings from retrospectives to future work

## Configuration

### Project Configuration
The integration is configured through:

```yaml
# .devsynth/project.yaml
cursor_integration:
  enabled: true
  rules_directory: ".cursor/rules"
  commands_directory: ".cursor/commands"
  modes_configured: true
  edrr_enhanced: true
  sdd_bdd_integration: true
```

### Development Workflow Configuration
```yaml
# config/default.yml
development_workflow:
  edrr_framework:
    enabled: true
    cursor_enhanced: true
    default_phase: expand
  specification_driven:
    sdd_enabled: true
    bdd_enabled: true
    cursor_commands_available: true
```

## Troubleshooting

### Common Issues

#### 1. Commands Not Available
**Problem**: Cursor commands are not showing up or working
**Solution**:
- Verify `.cursor/commands/` directory exists and contains `.md` files
- Check that Cursor IDE is properly configured
- Ensure project is loaded in Cursor workspace

#### 2. Rules Not Applying
**Problem**: Cursor rules are not providing expected guidance
**Solution**:
- Check that `.cursor/rules/` contains `.mdc` files with proper YAML frontmatter
- Verify rule file naming follows expected pattern (00-, 01-, etc.)
- Confirm `alwaysApply: true` for core rules

#### 3. Context Not Available
**Problem**: AI doesn't have access to project specifications or context
**Solution**:
- Ensure files are included in Cursor workspace
- Check that context management settings include required file patterns
- Verify memory system integration is working

### Performance Optimization
- **Context Management**: Configure appropriate file inclusion patterns
- **Model Selection**: Use appropriate models for different task types
- **Quality Gates**: Enable auto-run for common commands to reduce manual steps

## Migration Guide

### For Existing Projects
1. **Backup Current State**: Create backup of current project configuration
2. **Install Integration**: Copy `.cursor/` directory structure to project root
3. **Configure Settings**: Update `.devsynth/project.yaml` with Cursor integration settings
4. **Validate Setup**: Test integration with simple commands and workflows

### For New Projects
1. **Initialize Project**: Use `devsynth init` to create new project structure
2. **Enable Cursor Integration**: Copy `.cursor/` directory from DevSynth repository
3. **Configure Workflow**: Set up development workflow preferences
4. **Start Development**: Begin with specification creation and EDRR workflow

## Success Metrics

### Quantitative Metrics
- **Development Velocity**: 25% reduction in implementation time for new features
- **Code Quality**: 15% improvement in test coverage and specification compliance
- **Bug Reduction**: 30% reduction in post-implementation issues
- **Documentation**: 100% of new features have corresponding specifications and BDD tests

### Qualitative Metrics
- **Developer Experience**: Seamless integration between Cursor and DevSynth workflows
- **Specification Quality**: Clear, executable specifications that drive implementation
- **Agent Effectiveness**: More accurate and context-aware AI assistance
- **Team Collaboration**: Improved coordination and knowledge sharing

This integration transforms the development experience by providing structured AI assistance that enhances rather than replaces the established DevSynth development workflows and quality standards.
