# DevSynth Cursor IDE Rules

This directory contains modular Cursor IDE rules that provide AI-powered development guidance for the DevSynth project.

## Rules Structure

### Core Rules (Always Applied)

- **00-project-core.md** (`alwaysApply: true`)
  - Core philosophy and mandatory workflows
  - Environment setup and dependencies
  - Critical commands and verification
  - Applied to all files in the project

### Context-Specific Rules

Applied based on file patterns (globs):

- **01-testing-standards.md** (`tests/**/*`)
  - Speed markers (fast/medium/slow) - mandatory
  - Test organization and patterns
  - Mocking and coverage standards
  - Resource markers and flags

- **02-bdd-workflow.md** (`tests/behavior/**/*`, `docs/specifications/**/*`)
  - Specification-first BDD workflow
  - Socratic checklist requirements
  - Gherkin feature file conventions
  - Step definition patterns

- **03-security-compliance.md** (`src/**/*`, `scripts/**/*`)
  - Security policy compliance
  - Dialectical audit requirements
  - Encryption and TLS configuration
  - Vulnerability management

- **04-code-style.md** (`**/*.py`)
  - PEP 8 compliance
  - Type hints (mandatory for new code)
  - Docstring standards (Google style)
  - Formatting (Black, isort, flake8)

- **05-documentation.md** (`docs/**/*.md`)
  - Markdown front matter (mandatory)
  - Documentation structure
  - Traceability requirements
  - Metadata validation

- **06-commit-workflow.md** (`.git/**/*`, `.github/**/*`)
  - Conventional Commits (mandatory)
  - Pre-commit checklist
  - PR workflow and templates
  - Issue management

## How Cursor Uses These Rules

Cursor IDE's AI features (Agent, Inline Edit, Chat) use these rules as persistent context:

1. **00-project-core.md** is always included in AI context
2. Other rules activate based on the files you're working with
3. Rules provide guidance without requiring explicit prompts
4. Rules ensure consistency across AI-assisted development

## Rule Design Principles

Following Cursor IDE best practices:

- **Focused**: Each rule under 500 lines, single responsibility
- **Modular**: Composable rules for specific contexts
- **Actionable**: Concrete instructions and examples
- **Versioned**: Track changes with project
- **Validated**: Automatically tested via `validate-rules.py`

## Legacy Rules

The original single-file format has been backed up to `.cursor/rules.legacy` and replaced with this modular structure for:
- Better organization
- Easier maintenance
- Context-specific guidance
- Improved AI performance

## Multi-Disciplined Approach

These rules embody DevSynth's commitment to:

### Dialectical Reasoning
Every significant change considers:
- **Thesis**: Initial approach
- **Antithesis**: Challenges and alternatives
- **Synthesis**: Resolved solution

### Socratic Method
Every feature answers:
1. **What is the problem?**
2. **What proofs confirm the solution?**

### Systems Thinking
Rules interconnect to form a cohesive development system:
- Specifications → Tests → Code → Documentation
- Security → Audit → Compliance → Deployment
- Style → Quality → Maintainability → Collaboration

### Holistic Perspective
Considers the entire development lifecycle:
- Planning (specifications)
- Development (BDD workflow)
- Quality (testing, code style)
- Security (compliance, audits)
- Collaboration (commits, PRs)
- Maintenance (documentation)

## Workflow Integration

### For New Features

1. **Specification** (02-bdd-workflow.md)
   - Create spec in `docs/specifications/`
   - Answer Socratic checklist
   - Include dialectical analysis

2. **Failing Test** (02-bdd-workflow.md, 01-testing-standards.md)
   - Write BDD feature
   - Add speed markers
   - Implement step definitions

3. **Implementation** (04-code-style.md, 03-security-compliance.md)
   - Write code with type hints
   - Follow security policies
   - Add comprehensive docstrings

4. **Documentation** (05-documentation.md)
   - Update relevant docs
   - Include metadata
   - Maintain traceability

5. **Commit** (06-commit-workflow.md)
   - Use Conventional Commits
   - Run pre-commit checks
   - Resolve dialectical audit

## Validation

Rules are validated automatically:

```bash
# Validate rules format
python .cursor/validate-rules.py

# Verify rules are being applied
# (Check Cursor IDE's context panel when editing files)
```

## Updating Rules

When updating rules:

1. Keep each rule focused and under 500 lines
2. Update the `description` field
3. Adjust `globs` if file patterns change
4. Add concrete examples
5. Test with actual development scenarios
6. Run validation script

## References

- **Cursor IDE Best Practices**: https://cursor.directory/rules/best-practices
- **Project Documentation**: `docs/`
- **Contributing Guide**: `CONTRIBUTING.md`
- **Testing Standards**: `docs/TESTING_STANDARDS.md`

## Support

For questions about these rules or suggested improvements:
1. Review existing issues in `issues/`
2. Consult `docs/developer_guides/`
3. Open a new issue with `area/docs` label

## Version

Rules version: 0.1.0-alpha.1
Last updated: 2025-10-08
Maintained by: DevSynth Team

