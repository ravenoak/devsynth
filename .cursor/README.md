# DevSynth Cursor IDE Configuration

This directory contains Cursor IDE rules and configuration for effective AI-powered development within the DevSynth project.

## Structure Overview

DevSynth uses the modern Cursor IDE rules format with modular, context-specific rule files:

```
.cursor/
├── README.md                    # This file
├── CURSOR_INTEGRATION.md        # Comprehensive integration guide
├── rules/                       # Modular rules directory
│   ├── README.md                # Rules structure documentation
│   ├── 00-project-core.md       # Core rules (always applied)
│   ├── 01-testing-standards.md  # Testing guidelines
│   ├── 02-bdd-workflow.md       # BDD and specifications
│   ├── 03-security-compliance.md # Security and audit policies
│   ├── 04-code-style.md         # Code style standards
│   ├── 05-documentation.md      # Documentation requirements
│   ├── 06-commit-workflow.md    # Commits and PRs
│   └── workflows/               # Workflow guides
│       ├── adding-feature.md    # Feature development workflow
│       ├── fixing-bug.md        # Bug fix workflow
│       └── running-tests.md     # Testing workflow
├── rules.legacy                 # Backup of original single-file format
└── validate-rules.py            # Rules validation script
```

## Quick Start

### For Developers

1. **Read the Integration Guide**: Start with `CURSOR_INTEGRATION.md`
2. **Understand Core Rules**: Review `rules/00-project-core.md`
3. **Explore Workflows**: Check `rules/workflows/` for common tasks
4. **Use AI Assistance**: Cursor's AI will apply rules automatically

### For AI/LLM Agents

Rules are automatically loaded based on file context:
- **Core rules** (`00-project-core.md`) apply to all files
- **Specific rules** activate based on glob patterns (see each rule's front matter)
- **Workflow guides** provide step-by-step instructions for common tasks

## Key Features

### Multi-Disciplined Approach

Rules embody four complementary methodologies:

1. **Dialectical Reasoning** (thesis → antithesis → synthesis)
   - Consider alternatives and trade-offs
   - Document decision rationale
   - Synthesize best approaches

2. **Socratic Method** (question-driven development)
   - What is the problem?
   - What proofs confirm the solution?
   - Guide specification creation

3. **Systems Thinking** (interconnected components)
   - Understand ripple effects
   - Maintain consistency across system
   - Integrate changes holistically

4. **Holistic Perspective** (complete lifecycle)
   - Planning through deployment
   - Quality, security, maintainability
   - Collaboration and documentation

### Context-Aware Rules

Rules activate based on what you're working on:

| Files | Active Rules | Guidance |
|-------|--------------|----------|
| Any file | 00-project-core.md | Mandatory workflows, critical commands |
| `tests/**/*` | 01-testing-standards.md | Speed markers, test patterns, coverage |
| `tests/behavior/**/*` | 02-bdd-workflow.md | Specifications, Gherkin, step definitions |
| `src/**/*` | 03-security-compliance.md | Security policies, audit requirements |
| `**/*.py` | 04-code-style.md | PEP 8, type hints, docstrings |
| `docs/**/*.md` | 05-documentation.md | Front matter, metadata, traceability |
| `.git/**/*` | 06-commit-workflow.md | Conventional Commits, PR workflow |

### Workflow Integration

Complete workflows for common tasks:

- **Adding Features**: Specification → BDD → Implementation → Documentation
- **Fixing Bugs**: Reproduce → Failing Test → Fix → Regression Tests
- **Running Tests**: By speed, type, marker, with coverage

## Core Principles

### 1. Specification-First BDD (Non-Negotiable)

**Every feature must follow this sequence:**

1. Create specification in `docs/specifications/`
2. Answer Socratic checklist
3. Write failing BDD feature
4. Implement with tests
5. Update documentation

### 2. Test Discipline (Mandatory)

- **Exactly one speed marker** per test: `fast`, `medium`, or `slow`
- **Resource guards** for optional dependencies
- **Test organization** mirrors source structure
- **Coverage target**: ≥90% aggregate

### 3. Tool Integration

- **Poetry**: All Python commands via `poetry run`
- **go-task**: Common workflows via `task`
- **pre-commit**: Quality checks before commits
- **Verification scripts**: Test markers, traceability, audit

### 4. Quality Standards

- **Type hints**: Mandatory for all new code
- **Docstrings**: Google style for all public APIs
- **Formatting**: Black, isort, flake8
- **Security**: Bandit, Safety scans

### 5. Security & Compliance

- **Security Policy**: Follow `docs/policies/security.md`
- **Dialectical Audit**: Resolve before commits
- **Encryption**: At rest and in transit (for deployments)
- **Access Control**: Authentication, authorization, sanitization

### 6. Conventional Commits

```
type(scope): brief summary

Detailed explanation.

Dialectical notes (for significant changes):
- Thesis: Original approach
- Antithesis: Problem identified
- Synthesis: New solution

ReqID: FR-XX
Closes #issue
```

## How Cursor AI Uses Rules

### Automatic Context Loading

When you edit a file, Cursor loads relevant rules automatically:

1. Core rules always included
2. File-specific rules loaded based on globs
3. Workflow guides available on demand

### Intelligent Assistance

**Without explicit prompting, AI:**
- Suggests specification-first workflow
- Adds speed markers to tests
- Enforces code style standards
- Recommends security checks
- Maintains documentation sync

### Quality Prevention

**AI prevents common mistakes:**
- Missing speed markers on tests
- Code without specifications
- Commits without audit resolution
- Documentation without metadata
- Security policy violations

## Usage Examples

### Feature Development

```
You: "Add memory search feature"

AI (guided by rules):
1. "First, let's create a specification..."
2. "Now a failing BDD feature..."
3. "Let's implement with proper type hints..."
4. "Adding tests with speed markers..."
5. "Updating documentation..."
6. "Suggesting conventional commit..."
```

### Bug Fix

```
You: "Bug: memory leak in cache"

AI (guided by rules):
1. "Let's write a failing test first..."
2. "Verified test fails - proves bug exists"
3. "Implementing minimal fix..."
4. "Adding regression tests..."
5. "Running security checks..."
```

### Code Review

```
You: "Review this PR"

AI checks:
- Specification exists ✓
- Tests have speed markers ✓
- Code follows style guide ✓
- Documentation updated ✓
- Conventional commits used ✓
- Security compliant ✓
- Audit resolved ✓
```

## Integration with Existing Documentation

These Cursor rules complement DevSynth's existing documentation:

- **`CONTRIBUTING.md`**: Primary contribution guide
- **`docs/policies/`**: Security, audit, governance
- **`docs/specifications/`**: Technical specifications
- **`docs/architecture/`**: System design
- **`docs/TESTING_STANDARDS.md`**: Testing details

**Note**: `AGENTS.md` and `scripts/codex_setup.sh` are for Codex environments only and should NOT be referenced for Cursor IDE development.

## Validation

Validate rules structure and format:

```bash
python .cursor/validate-rules.py
```

## Maintenance

### When to Update Rules

- Development workflows change
- New tools or standards adopted
- Common AI mistakes identified
- Project structure evolves
- Best practices emerge

### How to Update Rules

1. Edit relevant rule file(s)
2. Keep each rule under 500 lines
3. Maintain clear, actionable guidance
4. Add concrete examples
5. Test with actual scenarios
6. Run validation script

### Version History

- **v1.0 (2025-10-08)**: Converted to modern modular format
  - Split single file into focused modules
  - Added workflow-specific guides
  - Created comprehensive integration documentation
  - Backed up legacy format to `rules.legacy`

## Success Metrics

Effective Cursor AI assistance means:

1. ✅ Follows BDD workflow without prompting
2. ✅ Maintains test marker discipline automatically
3. ✅ Uses correct command patterns consistently
4. ✅ Organizes files in appropriate directories
5. ✅ Meets quality and security requirements
6. ✅ Integrates seamlessly with tooling
7. ✅ Provides helpful, project-specific guidance

## Getting Help

- **Integration guide**: Read `CURSOR_INTEGRATION.md`
- **Rule details**: See `rules/README.md`
- **Workflows**: Check `rules/workflows/`
- **Project docs**: Consult `docs/`
- **Issues**: Open in `issues/` with `area/docs` label

## Philosophy

DevSynth's rules system ensures AI assistance is:

- **Consistent**: All code follows project standards
- **Quality-Focused**: Multiple quality gates enforced
- **Efficient**: Workflows streamlined, mistakes prevented
- **Collaborative**: Team alignment through shared standards
- **Maintainable**: Long-term project health prioritized

By combining dialectical reasoning, Socratic questioning, systems thinking, and holistic perspective, we achieve thoughtful, purposeful, integrated, and complete development.
