# Cursor IDE Integration

This directory contains Cursor IDE configuration files that integrate DevSynth's agentic development workflows with Cursor's AI assistance capabilities.

## Overview

The Cursor integration enhances DevSynth's development experience by providing structured AI assistance that aligns with the project's established methodologies:

- **EDRR Framework**: Expand, Differentiate, Refine, Retrospect development cycle
- **SDD + BDD**: Specification-Driven Development with Behavior-Driven Development
- **Multi-Agent Collaboration**: WSDE (Worker Self-Directed Enterprise) model
- **Quality Assurance**: Comprehensive testing, security, and compliance checking

## Directory Structure

### Rules (`.cursor/rules/`)
Comprehensive rules system that guides AI behavior throughout the development lifecycle:

#### Core Rules (Always Applied)
- **`00-architecture.mdc`**: Project constitution and core architectural principles (always active)
- **`00-project-core.md`**: Core project philosophy, setup, and development workflow (always active)
- **`01-edrr-framework.mdc`**: EDRR phase guidance and structured thinking methodology (always active)
- **`02-specification-driven.mdc`**: Specification-Driven Development (SDD) + BDD integration (always active)

#### Context-Specific Rules (Auto-Attach)
- **`01-testing-standards.md`**: Applied when working with test files - comprehensive testing standards
- **`02-bdd-workflow.md`**: Applied when working with BDD features and step definitions
- **`03-security-compliance.md`**: Applied to all source code - security requirements and validation
- **`03-testing-philosophy.mdc`**: Applied when working with tests - testing philosophy and practices
- **`04-code-style.md`**: Applied to all Python code - formatting and style standards
- **`07-poetry-environment.md`**: Applied when working with dependency files - Poetry and environment management

#### Specialized Rules (Manual Invocation)
- **`04-security-compliance.mdc`**: Deep security analysis - invoke with @security-analysis
- **`05-dialectical-reasoning.mdc`**: Dialectical reasoning for decisions - invoke with @dialectical-audit
- **`06-commit-workflow.md`**: Git workflow guidance - invoke with @commit-guidance

#### Workflow Rules
- **`workflows/adding-feature.md`**: Feature development workflow guidance
- **`workflows/fixing-bug.md`**: Bug fixing workflow guidance
- **`workflows/running-tests.md`**: Testing workflow guidance

### Commands (`.cursor/commands/`)
Structured workflow commands for systematic development:

#### EDRR Workflow Commands
- **`expand-phase.md`**: Generate multiple diverse approaches and explore alternatives
- **`differentiate-phase.md`**: Analyze and compare approaches with multi-criteria evaluation
- **`refine-phase.md`**: Implement and optimize selected solutions with comprehensive testing
- **`retrospect-phase.md`**: Analyze outcomes and capture learnings for continuous improvement

#### Specification and Testing Commands
- **`generate-specification.md`**: Create comprehensive SDD specifications and BDD scenarios
- **`validate-bdd-scenarios.md`**: Validate Gherkin syntax, content quality, and implementation feasibility
- **`generate-test-suite.md`**: Create comprehensive test coverage (unit, integration, BDD)
- **`code-review.md`**: Perform comprehensive code review and quality assessment

#### Development Workflow Commands
- **`fix-bdd-syntax.md`**: Fix common BDD/Gherkin syntax issues
- **`add-speed-markers.md`**: Add appropriate speed markers to tests
- **`update-specifications.md`**: Update specifications to reflect implementation changes

### Custom Modes (`.cursor/modes.json`)
Specialized Cursor modes optimized for DevSynth workflows:

- **EDRRImplementer** (`Cmd+Shift+E`): Implementation within EDRR framework with comprehensive testing
- **SpecArchitect** (`Cmd+Shift+S`): Specification and BDD scenario creation for SDD workflow
- **TestArchitect** (`Cmd+Shift+T`): Comprehensive test suite creation and validation
- **CodeReviewer** (`Cmd+Shift+R`): Comprehensive code review and quality assessment
- **DialecticalThinker** (`Cmd+Shift+D`): Apply dialectical reasoning and multi-perspective analysis

### Integration Files
- **`CURSOR_SETUP.md`**: Comprehensive setup guide with platform-specific instructions
- **`CURSOR_INTEGRATION.md`**: Integration troubleshooting and best practices
- **`integration-test.md`**: Integration testing scenarios and validation
- **`README.md`**: This overview document

## Usage Guidelines

### Daily Development Workflow

1. **Environment Setup**: Ensure Poetry environment is active (`poetry run` prefix for all commands)
2. **Context Loading**: Open project in Cursor to automatically load rules and context
3. **Specification Check**: Review relevant specifications in `docs/specifications/`
4. **EDRR Process**: Use structured commands for systematic development
5. **Quality Gates**: Run tests and validation before committing

### Command Usage

Use commands with the `/` prefix in Cursor chat interface:

#### EDRR Workflow Commands
```bash
/expand-phase implement user authentication system
# Generates multiple approaches: OAuth2, JWT tokens, API keys, etc.

/differentiate-phase authentication approaches security analysis
# Compares approaches by security, complexity, performance, maintenance

/refine-phase implement OAuth2 with FastAPI Security
# Implements selected approach with comprehensive testing

/retrospect-phase authentication implementation lessons learned
# Analyzes outcomes and captures improvements
```

#### Specification and Testing Commands
```bash
/generate-specification user profile management feature
# Creates specification in docs/specifications/ and BDD scenarios in tests/behavior/features/

/validate-bdd-scenarios user_profile_management.feature
# Validates Gherkin syntax, content quality, and technical feasibility

/generate-test-suite user profile component
# Creates unit tests, integration tests, and BDD scenarios with proper speed markers

/code-review recent user profile implementation changes
# Performs comprehensive code review with security and performance analysis
```

#### Development Workflow Commands
```bash
/fix-bdd-syntax tests/behavior/features/user_profile_management.feature
# Fixes common Gherkin syntax issues

/add-speed-markers tests/unit/test_user_profile.py
# Adds appropriate speed markers (@pytest.mark.fast/medium/slow)

/update-specifications user profile management implementation details
# Updates specifications to reflect actual implementation
```

### Custom Modes Usage

#### EDRRImplementer Mode (`Cmd+Shift+E`)
- **When to Use**: Implementing new features, refactoring components
- **Features**: Structured implementation guidance, automatic test generation
- **Workflow**: Start here for most development tasks

#### SpecArchitect Mode (`Cmd+Shift+S`)
- **When to Use**: Defining new features, creating specifications
- **Features**: SDD workflow guidance, BDD scenario generation
- **Workflow**: Use for specification-first development

#### TestArchitect Mode (`Cmd+Shift+T`)
- **When to Use**: Building comprehensive test suites, improving coverage
- **Features**: Unit, integration, and BDD test generation
- **Workflow**: Use when enhancing testing infrastructure

#### CodeReviewer Mode (`Cmd+Shift+R`)
- **When to Use**: Code reviews, quality assessments, security audits
- **Features**: Architecture compliance, security analysis, performance review
- **Workflow**: Use for quality assurance and improvement

#### DialecticalThinker Mode (`Cmd+Shift+D`)
- **When to Use**: Complex architectural decisions, trade-off analysis
- **Features**: Multi-perspective analysis, thesis-antithesis-synthesis
- **Workflow**: Use for critical decision-making

### Rule Application Strategy

#### Always-Apply Rules
- **00-architecture.mdc**: Provides project constitution and architectural principles
- **00-project-core.md**: Core philosophy, Poetry environment, and workflow standards
- **01-edrr-framework.mdc**: EDRR methodology and structured thinking guidance
- **02-specification-driven.mdc**: SDD + BDD integration and intent-driven development

#### Context-Aware Rules
- **01-testing-standards.md**: Activates when working with test files
- **02-bdd-workflow.md**: Activates when working with BDD features and step definitions
- **03-security-compliance.md**: Activates for all source code security validation
- **07-poetry-environment.md**: Activates when working with dependency management files

#### Manual Rule Invocation
Use `@rule-name` syntax in Cursor chat for specialized guidance:
- `@dialectical-audit`: For complex decision analysis
- `@security-analysis`: For deep security review
- `@commit-guidance`: For Git workflow assistance

## Integration Benefits

### Enhanced Developer Experience
- **Structured Guidance**: Clear workflows for complex development tasks with step-by-step assistance
- **Quality Assurance**: Built-in compliance with project standards and automated quality gates
- **Context Awareness**: AI assistance that understands project architecture, patterns, and specifications
- **Consistency**: Standardized approaches across all development activities with enforced best practices
- **Platform Integration**: Seamless integration with Poetry environments and development tools

### Methodology Alignment
- **EDRR Framework**: Structured thinking process for all development decisions with guided workflows
- **SDD + BDD**: Intent-driven development with executable specifications and automated scenario generation
- **Multi-Agent Collaboration**: Enhanced coordination between human and AI agents with specialized modes
- **Continuous Improvement**: Learning integration from retrospective analysis with improvement suggestions

### Quality Standards Integration
- **Testing**: Comprehensive test generation and validation with speed markers and resource gating
- **Security**: Built-in security compliance checking with automated vulnerability detection
- **Performance**: Performance consideration in all implementations with optimization suggestions
- **Documentation**: Living documentation that evolves with code and maintains traceability

## Platform-Specific Integration

### macOS Integration (Recommended)
- **Python Location**: `/opt/homebrew/bin/python3.12` (Homebrew installation)
- **Poetry Configuration**: In-project virtual environments with automatic activation
- **Development Tools**: Full compatibility with all testing and quality tools
- **Resource Access**: All optional dependencies available (kuzu, faiss-cpu, chromadb)

### Linux Integration
- **Python Location**: System Python 3.12 or pyenv-managed installation
- **Package Management**: Support for both apt and conda package managers
- **Development Tools**: Full compatibility with testing and quality tools
- **Resource Access**: Most optional dependencies available (platform-specific restrictions apply)

### Windows Integration
- **Python Location**: Python 3.12 from python.org (ensure PATH configuration)
- **Virtual Environments**: Poetry-managed environments with some limitations
- **Development Tools**: Compatible with core development workflow
- **Resource Access**: Limited optional dependencies (focus on essential features)

## Development Environment Integration

### Poetry Environment Management
- **Automatic Activation**: Virtual environment managed by Poetry with in-project configuration
- **Dependency Groups**: Organized extras for different development scenarios (dev, tests, api, etc.)
- **Platform Markers**: Automatic handling of platform-specific dependencies
- **Environment Validation**: Comprehensive validation scripts for environment integrity

### Testing Integration
- **Speed Markers**: All tests require speed markers (fast, medium, slow) for optimal execution
- **Resource Gating**: Optional dependencies gated by environment variables
- **Parallel Execution**: Configured for parallel test execution based on speed markers
- **Coverage Integration**: Built-in coverage reporting with quality gates

### Quality Assurance Integration
- **Pre-commit Hooks**: Automatic code quality checks before commits
- **Linting and Type Checking**: Integrated mypy, black, isort, and flake8
- **Security Scanning**: Built-in bandit and safety checks
- **Validation Scripts**: Comprehensive project validation before commits

## Configuration Management

The integration is configured through:
- **Project Constitution**: `constitution.md` provides project-wide governance and standards
- **Poetry Configuration**: `pyproject.toml` and `poetry.toml` define dependencies and environment
- **Cursor Rules**: `.cursor/rules/` directory contains comprehensive development guidance
- **AGENTS.md**: Enhanced with Cursor-specific guidance, workflows, and platform instructions
- **Configuration Files**: `config/` directory contains environment-specific settings

## Getting Started

### Quick Setup
1. **Install Prerequisites**: Python 3.12, Poetry, and Cursor IDE
2. **Clone Repository**: `git clone <repository-url> && cd devsynth`
3. **Setup Environment**: Follow platform-specific instructions in `CURSOR_SETUP.md`
4. **Verify Integration**: Run `poetry run python scripts/verify_cursor_integration.py`
5. **Start Development**: Use `/expand-phase` for your first feature implementation

### First Feature Development
```bash
# 1. Create specification
/generate-specification my new feature

# 2. Implement with EDRR process
/expand-phase implement my new feature
/differentiate-phase feature implementation approaches
/refine-phase implement selected approach
/retrospect-phase implementation analysis

# 3. Test and validate
poetry run devsynth run-tests --speed=fast
/generate-test-suite my new feature
```

## Best Practices

1. **Environment First**: Always verify Poetry environment before development (`poetry run python --version`)
2. **Specification Driven**: Check `docs/specifications/` before implementing any feature
3. **EDRR Process**: Use structured approach for all development tasks with Cursor commands
4. **Test Integration**: Write failing tests before implementation, use speed markers
5. **Quality Gates**: Run validation scripts before committing (`scripts/verify_*.py`)
6. **Platform Consistency**: Use consistent environment setup across team members
7. **Documentation Updates**: Keep specifications and documentation synchronized with code
8. **Security Awareness**: Follow security rules and run security validation

## Troubleshooting

### Quick Diagnostics
```bash
# Verify complete integration
poetry run python scripts/verify_cursor_integration.py

# Check environment
poetry run python scripts/check_dev_environment.py

# Validate test markers
poetry run python scripts/verify_test_markers.py

# Check requirements traceability
poetry run python scripts/verify_requirements_traceability.py
```

### Common Issues
- **Rules Not Applying**: Check YAML frontmatter in `.cursor/rules/*.mdc` files
- **Commands Not Available**: Verify `.cursor/commands/` directory exists and contains `.md` files
- **Environment Issues**: Recreate Poetry environment with `poetry env remove --all && poetry install`
- **Testing Problems**: Check speed markers and environment variables for optional resources

### Getting Help
1. **Documentation**: Check `CURSOR_SETUP.md` and `docs/developer_guides/cursor_integration.md`
2. **Validation Scripts**: Use diagnostic scripts in `scripts/` directory
3. **Community**: Review project issues and discussions for Cursor IDE topics
4. **Environment Report**: Generate comprehensive diagnostics with validation scripts

---

This integration transforms Cursor IDE into a comprehensive development environment that seamlessly combines AI assistance with DevSynth's structured methodologies. The result is enhanced developer productivity, consistent quality standards, and maintainable code that follows established architectural patterns and best practices.

For detailed setup instructions, see `CURSOR_SETUP.md`. For troubleshooting, refer to the validation scripts and diagnostic tools in the `scripts/` directory.
