# Cursor IDE Integration Guide for DevSynth

## Overview

This guide explains how Cursor IDE's AI features integrate with DevSynth's comprehensive rules system to provide intelligent, context-aware development assistance.

## What Are Cursor IDE Rules?

Cursor IDE rules are persistent instructions that guide the AI (Agent, Inline Edit, Chat) to understand your project's:
- Development workflows
- Coding standards
- Testing requirements
- Security policies
- Documentation practices

## DevSynth Rules Architecture

### Multi-Disciplined Foundation

DevSynth's rules embody a multi-disciplined approach to software development:

#### 1. Dialectical Reasoning
Every significant decision considers:
- **Thesis**: Initial approach or assumption
- **Antithesis**: Challenges, alternatives, counterpoints
- **Synthesis**: Resolved approach incorporating insights

**Example in Practice:**
When the AI suggests a solution, it considers trade-offs and alternatives, not just the first viable approach.

#### 2. Socratic Method
Every feature development answers:
- **What is the problem?** (Clear problem statement)
- **What proofs confirm the solution?** (Testable acceptance criteria)

**Example in Practice:**
AI ensures specifications exist before code, with clear problem definitions and success criteria.

#### 3. Systems Thinking
Understanding interconnections:
- Specifications → Tests → Code → Documentation
- Changes ripple through the system predictably
- Quality gates enforce consistency

**Example in Practice:**
AI reminds you to update related documentation, traceability links, and test markers when making changes.

#### 4. Holistic Perspective
Considering the entire development lifecycle:
- Planning (specifications)
- Development (BDD workflow)
- Quality (testing, style)
- Security (compliance, audits)
- Collaboration (commits, PRs)
- Maintenance (documentation)

**Example in Practice:**
AI doesn't just generate code—it ensures the code fits within the complete development process.

## Rules Structure

### Core Rules (Always Active)

**`00-project-core.md`** - Foundation for all development
- Applied to every file in the project
- Contains mandatory workflows and critical commands
- Enforces specification-first BDD approach
- Defines environment requirements

### Context-Specific Rules

Rules activate based on what you're working with:

| Rule File | Applies When | Key Guidance |
|-----------|--------------|--------------|
| `01-testing-standards.md` | Working with tests | Speed markers, test patterns, coverage |
| `02-bdd-workflow.md` | Specifications, features | Socratic checklist, Gherkin conventions |
| `03-security-compliance.md` | Source code, scripts | Security policies, audit requirements |
| `04-code-style.md` | Python files | PEP 8, type hints, docstrings |
| `05-documentation.md` | Markdown docs | Front matter, metadata, traceability |
| `06-commit-workflow.md` | Git operations | Conventional Commits, PR workflow |

### Workflow Guides

Detailed step-by-step workflows in `.cursor/rules/workflows/`:

- **`adding-feature.md`**: Complete feature development workflow
- **`fixing-bug.md`**: Test-first bug fix methodology
- **`running-tests.md`**: Comprehensive testing guide

## How Cursor AI Uses These Rules

### 1. Contextual Awareness

When you open a file, Cursor loads relevant rules:

```
Open: src/devsynth/application/memory/multi_layered.py
↓
Loads: 00-project-core.md (always)
       03-security-compliance.md (src/**/*.py)
       04-code-style.md (**/*.py)
```

### 2. Proactive Guidance

AI provides guidance without explicit prompts:

**Example 1: Adding a Feature**
```
You: "Create a new memory search feature"

AI (informed by rules):
1. First, let's create a specification in docs/specifications/
2. It must answer the Socratic checklist
3. Then we'll write a failing BDD feature
4. Finally implement with proper type hints and docstrings
```

**Example 2: Writing Tests**
```
You: "Write a test for this function"

AI (informed by rules):
- Includes exactly one speed marker (@pytest.mark.fast)
- Follows Arrange-Act-Assert pattern
- Adds ReqID reference in docstring
- Uses proper fixture patterns
```

### 3. Quality Enforcement

AI prevents common mistakes:

❌ **Without Rules:**
```python
def test_something():  # Missing speed marker
    # No docstring
    result = function()  # No AAA pattern
    assert result
```

✅ **With Rules:**
```python
@pytest.mark.fast
def test_something_succeeds_with_valid_input():
    """ReqID: FR-01 - Feature processes valid input correctly."""
    # Arrange
    instance = MyClass()
    valid_input = "test"
    
    # Act
    result = instance.process(valid_input)
    
    # Assert
    assert result == expected_value
```

### 4. Workflow Integration

AI guides you through complete workflows:

**Feature Development:**
1. Checks if specification exists → prompts to create if missing
2. Checks if BDD feature exists → prompts to create if missing
3. Verifies failing test → ensures TDD approach
4. Implements code with proper style → enforces standards
5. Reminds about documentation → maintains traceability
6. Suggests conventional commit → enforces commit standards

## Using Cursor AI Effectively

### Chat Window

Ask questions informed by project context:

```
You: "How do I add a new memory backend?"

AI response includes:
- Specification-first workflow
- Required interfaces to implement
- Test patterns with speed markers
- Security considerations
- Documentation requirements
```

### Inline Edit

Edit code with AI assistance:

```
You: Select function → Cmd+K → "Add type hints and docstring"

AI generates:
- Proper type hints (from 04-code-style.md)
- Google-style docstring (from 04-code-style.md)
- Includes Args, Returns, Raises sections
- Adds usage example
```

### Agent

Full-featured development assistance:

```
You: "Implement user authentication feature"

AI workflow (guided by rules):
1. Creates specification answering Socratic checklist
2. Includes dialectical analysis of approaches
3. Creates failing BDD feature with scenarios
4. Writes step definitions following patterns
5. Implements with security compliance
6. Adds comprehensive tests with markers
7. Updates documentation with metadata
8. Suggests conventional commit message
9. Checks dialectical audit status
```

## Rule Customization

### Adding Project-Specific Rules

Create new rule files in `.cursor/rules/`:

```markdown
---
description: Custom rule for your specific needs
globs:
  - "specific/path/**/*"
alwaysApply: false
---

# Your Custom Rule

Content here...
```

### Updating Existing Rules

1. Edit relevant rule file
2. Keep under 500 lines (best practice)
3. Maintain clear, actionable guidance
4. Add concrete examples
5. Test with actual development scenarios

### Rule Priorities

Rules combine when multiple match:
1. Core rules (00-project-core.md) always apply
2. More specific globs take precedence
3. Later rules can augment earlier ones

## Verification and Validation

### Check Rules Are Working

1. **Open a test file**: Should see testing standards apply
2. **Ask AI about workflow**: Should reference specific rules
3. **Request code generation**: Should follow style guide
4. **Check commit messages**: Should suggest Conventional Commits

### Validate Rules Format

```bash
# Run validation script
python .cursor/validate-rules.py

# Check for issues
```

### Monitor AI Context

Check Cursor's context panel to see which rules are active for current file.

## Best Practices

### 1. Trust the Workflow

Don't skip steps AI recommends—they're there for good reasons:
- Specifications prevent wasted implementation effort
- Failing tests ensure TDD discipline
- Security checks prevent vulnerabilities
- Documentation maintains long-term maintainability

### 2. Provide Context

Help AI help you:
```
Good: "Implement memory search following BDD workflow"
Better: "Implement memory search. I've created the specification in docs/specifications/memory_search.md"
```

### 3. Leverage Dialectical Thinking

When AI suggests an approach, engage dialectically:
```
You: "What are the trade-offs of this approach?"
AI: Explains thesis, antithesis, provides synthesis
```

### 4. Use Socratic Questions

Frame requests as problem statements:
```
Good: "What problem does this solve?"
Then: "How do we prove it works?"
```

## Common Scenarios

### Starting a New Feature

```
You: "@agent I need to add <feature>"

AI will guide through:
1. Specification creation
2. Socratic checklist
3. Dialectical analysis
4. BDD feature file
5. Implementation with tests
6. Documentation updates
7. Commit workflow
```

### Fixing a Bug

```
You: "Bug: <description>"

AI will guide through:
1. Reproduction test (should fail)
2. Root cause analysis
3. Minimal fix implementation
4. Regression tests
5. Documentation updates
```

### Code Review Assistance

```
You: "Review this PR for DevSynth standards"

AI checks:
- Specification exists
- Tests have speed markers
- Code follows style guide
- Documentation updated
- Conventional commits used
- Security compliance
```

## Troubleshooting

### AI Not Following Rules

1. Check rule globs match your files
2. Verify rules are valid markdown
3. Check `.cursor/rules/README.md` for structure
4. Restart Cursor IDE

### Conflicting Guidance

Rules are designed to be complementary. If you encounter conflicts:
1. Core rules (00-project-core.md) take precedence
2. More specific rules augment general ones
3. Report genuine conflicts as issues

### Rules Too Restrictive

Rules enforce project standards. If a standard seems wrong:
1. Discuss with team
2. Update rule if consensus reached
3. Document rationale for change

## Integration with Other Tools

### Pre-Commit Hooks

Cursor rules align with pre-commit hooks:
- AI suggests fixes for hook failures
- Understands hook requirements
- Guides to proper solutions

### CI/CD Pipeline

Rules mirror CI requirements:
- Speed markers match CI test selection
- Security checks align with CI audits
- Documentation standards match CI validation

### IDE Features

Combine rules with IDE features:
- Run tests suggested by AI
- Navigate to files AI references
- Use inline edits with rule guidance

## Advanced Usage

### Workflow Chaining

AI can execute multi-step workflows:

```
You: "Implement feature X from issue #123"

AI executes:
1. Reads issue
2. Creates specification
3. Writes failing tests
4. Implements feature
5. Updates documentation
6. Prepares commit
7. Suggests PR description
```

### Context Building

Help AI understand complex scenarios:

```
You: "Context: Working on memory system refactoring"
    "Goal: Add caching layer"
    "Follow BDD workflow"

AI response incorporates:
- Memory system architecture
- BDD workflow requirements
- Security considerations
- Testing patterns
```

### Rule-Aware Refactoring

```
You: "Refactor this maintaining DevSynth standards"

AI ensures:
- Tests updated (with markers)
- Type hints preserved/improved
- Docstrings updated
- Security not compromised
- Documentation synchronized
```

## Continuous Improvement

### Feedback Loop

Rules evolve with project:
1. Encounter pattern not covered → add to rules
2. Find rule unclear → clarify with examples
3. Discover better approach → update rule
4. Patterns change → rules change

### Rule Metrics

Consider tracking:
- How often AI references rules correctly
- Common deviations requiring correction
- Workflow compliance rates
- Quality metrics (coverage, lint, security)

## Conclusion

Cursor IDE rules transform AI assistance from generic to project-specific, ensuring:
- **Consistency**: All code follows project standards
- **Quality**: Multiple quality gates enforced
- **Efficiency**: Workflows streamlined, mistakes prevented
- **Collaboration**: Team alignment through shared standards
- **Maintainability**: Long-term project health

The multi-disciplined approach (dialectical, Socratic, systems, holistic thinking) ensures development is:
- **Thoughtful**: Considers alternatives and trade-offs
- **Purposeful**: Solves clear, well-defined problems
- **Integrated**: Changes ripple through system appropriately
- **Complete**: Lifecycle from concept to documentation covered

By leveraging these rules effectively, you'll develop better software faster, with fewer mistakes and greater confidence.

