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

- **07-cursor-rules-management.md** (`.cursor/**/*`, `**/*.md`)
  - Cursor IDE rules management and validation
  - Rule development workflow
  - Troubleshooting and maintenance

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

DevSynth's rules implement a rigorous multi-disciplined framework that integrates philosophy, methodology, and engineering practice:

### Dialectical Reasoning (Hegelian)
Every significant decision follows the dialectic:
- **Thesis**: Initial hypothesis or approach
- **Antithesis**: Critical examination, challenges, and counter-arguments
- **Synthesis**: Resolved solution that transcends and includes both

**Applied throughout development:**
```markdown
## Dialectical Analysis for New Feature

**Thesis**: Build monolithic CLI for simplicity
**Antithesis**: Monoliths become unmaintainable at scale
**Synthesis**: Modular CLI with plugin architecture for extensibility
```

### Socratic Method (Classical Philosophy)
Every feature specification answers the Socratic triad:
1. **What is the problem?** (Clear problem definition)
2. **What proofs confirm the solution?** (Evidence-based validation)
3. **What are the implications?** (Holistic impact assessment)

### Systems Thinking (General Systems Theory)
Rules form an interconnected ecosystem where changes propagate through the system:
- **Specifications** drive **BDD tests** which validate **implementation**
- **Security policies** integrate with **audit processes** ensuring **compliance**
- **Code style** standards enable **quality assurance** supporting **maintainability**

### Holistic Perspective (Gestalt Psychology)
Considers the entire development ecosystem simultaneously:
- **Planning**: Specification-first approach with dialectical analysis
- **Development**: BDD workflow with TDD integration
- **Quality**: Multi-layered testing (unit → integration → behavior)
- **Security**: Defense-in-depth with audit and compliance
- **Collaboration**: Conventional commits with PR workflow
- **Maintenance**: Documentation with traceability and validation

### Pragmatic Engineering (Deweyan Instrumentalism)
Rules serve practical purposes while remaining adaptable:
- **Instrumental**: Each rule solves real development problems
- **Experimental**: Rules evolve based on observed outcomes
- **Contextual**: Applied differently based on situation (fast unit tests vs. slow integration tests)
- **Consequential**: Success measured by development velocity and product quality

### Integration Across Disciplines

**Philosophy → Methodology → Practice:**
- Dialectical reasoning enables robust decision-making
- Socratic method ensures problem clarity
- Systems thinking prevents unintended consequences
- Holistic perspective maintains ecosystem health
- Pragmatic engineering delivers working software

**Quality Gates with Multi-Disciplinary Validation:**
1. **Philosophical**: Socratic checklist completed
2. **Methodological**: BDD scenarios pass
3. **Technical**: All quality checks pass (lint, type, test)
4. **Security**: Audit log resolved
5. **Collaborative**: PR approved with conventional commits

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
Last updated: 2025-10-16
Maintained by: DevSynth Team

## Critical Evaluation Summary

**Multi-Disciplined Enhancement (2025-10-16):**

This ruleset has been critically evaluated using dialectical and Socratic reasoning, resulting in comprehensive enhancements:

### Dialectical Analysis Applied
- **Thesis**: Original rules were functional but lacked depth in multi-disciplined integration
- **Antithesis**: Rules needed stronger philosophical foundation and practical guidance
- **Synthesis**: Enhanced ruleset integrating philosophy, methodology, and engineering practice

### Key Enhancements
1. **Philosophy Integration**: Explicit multi-disciplined approach with Hegelian dialectic, Socratic method, systems thinking
2. **Practical Guidance**: Concrete examples, workflow guidance, and troubleshooting
3. **Environment Management**: Dedicated Poetry/virtual environment rule with comprehensive setup
4. **Quality Assurance**: Automated validation with fixed Poetry extras checking
5. **Documentation**: Enhanced metadata, examples, and cross-references

### Validation Framework
- Automated rule validation via `validate-rules.py`
- Comprehensive project structure verification
- Poetry configuration alignment checking
- Real-time feedback for rule compliance

### Holistic Coverage
- **Planning**: Specification-first BDD workflow
- **Development**: Multi-layered testing with speed markers
- **Quality**: Code style, type hints, comprehensive testing
- **Security**: Defense-in-depth with dialectical audit
- **Collaboration**: Conventional commits with PR workflow
- **Maintenance**: Documentation with traceability
