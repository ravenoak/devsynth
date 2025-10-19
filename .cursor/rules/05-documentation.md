---
description: Documentation standards and metadata requirements
globs:
  - "docs/**/*.md"
  - "README.md"
  - "CONTRIBUTING.md"
alwaysApply: false
---

# DevSynth Documentation Standards

## Documentation Structure

```
docs/
├── specifications/        # Feature specifications
├── policies/              # Project policies
├── architecture/          # Architecture docs
├── developer_guides/      # Developer guides
├── user_guides/           # User guides
├── api_reference/         # API documentation
└── testing/               # Testing guides
```

## Markdown Front Matter

**All markdown documents must include front matter:**

```markdown
---
title: "<Document Title>"
date: "YYYY-MM-DD"
version: "0.1.0-alpha.1"
tags:
  - "tag1"
  - "tag2"
status: "published|draft"
author: "DevSynth Team"
last_reviewed: "YYYY-MM-DD"
---

# Document Title

Content here...
```

Validate with:
```bash
poetry run devsynth validate-metadata <file>
```

## Markdown Style

### Headings

Use ATX-style headings:
```markdown
# Heading 1
## Heading 2
### Heading 3
```

### Lists

```markdown
- Unordered item 1
- Unordered item 2
  - Nested item

1. Ordered item 1
2. Ordered item 2
```

### Code Blocks

Use fenced code blocks with language identifiers:

````markdown
```python
def example():
    """Example function."""
    return "Hello"
```

```bash
poetry run devsynth --help
```
````

### Links

```markdown
[Link text](url)
[Internal link](../other/doc.md)
```

## Documentation Types

### Specifications

Location: `docs/specifications/`

Must answer Socratic checklist:
1. What is the problem?
2. What proofs confirm the solution?

Include:
- Problem statement
- Solution overview
- Dialectical analysis
- Requirements (FR-XX, NFR-XX)
- Acceptance criteria
- Traceability links

### Policies

Location: `docs/policies/`

Must include:
- Clear policy statement
- Rationale
- Implementation guidance
- Enforcement mechanism
- Review cadence

### Architecture Docs

Location: `docs/architecture/`

Include:
- Component diagrams
- Interaction patterns
- Design decisions
- Trade-offs and alternatives

### User Guides

Location: `docs/user_guides/`

Must be:
- Task-oriented
- Step-by-step
- Include examples
- Tested procedures

### Developer Guides

Location: `docs/developer_guides/`

Include:
- Setup instructions
- Development workflows
- Code examples
- Troubleshooting

## Line Length

Keep lines to 80-120 characters for readability.

## Documentation Policies

Follow `docs/policies/documentation_policies.md`:
- Use system time for dates
- Keep documentation synchronized with code
- Review quarterly
- Link related documents

## Breadcrumbs

Include breadcrumb navigation:

```markdown
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt;
<a href="index.md">Section</a> &gt;
Current Document
</div>
```

## Traceability

Link specifications to:
- Feature files: `tests/behavior/features/`
- Implementation: `src/devsynth/`
- Requirements: FR-XX, NFR-XX
- Issues: `issues/<id>.md`

Verify with:
```bash
poetry run python scripts/verify_requirements_traceability.py
```

## Documentation Templates

Available in `templates/`:
- `DOCUMENTATION_TEMPLATE.md`
- `FEATURE_IMPLEMENTATION_PLAN_TEMPLATE.md`

## Metadata Validation

```bash
# Validate single file
poetry run devsynth validate-metadata docs/example.md

# Validate all docs
find docs -name "*.md" -exec poetry run devsynth validate-metadata {} \;
```

## Documentation Maintenance

### Review Schedule

- Quarterly review of all policies
- Update `last_reviewed` field
- Track in `docs/policies/documentation_review_schedule.md`

### Ownership

Follow `docs/policies/documentation_ownership.md`:
- Assign owners to documentation sections
- Define review responsibilities

## Best Practices

### Do:
- ✅ Use clear, concise language
- ✅ Include examples
- ✅ Keep docs synchronized with code
- ✅ Use front matter metadata
- ✅ Link related documents
- ✅ Test all code examples

### Don't:
- ❌ Use vague language
- ❌ Omit front matter
- ❌ Leave docs outdated
- ❌ Include untested examples
- ❌ Use relative dates ("recently", "soon")

## Documentation Commands

```bash
# Build documentation site
poetry run mkdocs build

# Serve locally
poetry run mkdocs serve

# Validate metadata
poetry run devsynth validate-metadata docs/**/*.md

# Generate API docs
poetry run python scripts/generate_api_docs.py
```

## MkDocs Configuration

Configuration in `mkdocs.yml`:
- Material theme
- Plugin: mkdocstrings-python
- Plugin: gen-files
- Plugin: include-markdown
- Plugin: typer2
