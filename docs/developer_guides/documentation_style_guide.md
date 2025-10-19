---

title: "DevSynth Documentation Style Guide"
date: "2025-08-02"
version: "0.1.0-alpha.1"
tags:
  - "documentation"
  - "style guide"
  - "best practices"
  - "formatting"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-02"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; DevSynth Documentation Style Guide
</div>

# DevSynth Documentation Style Guide

## Executive Summary

This style guide establishes standards for creating and maintaining documentation in the DevSynth project. It covers formatting conventions, file organization, cross-referencing practices, and writing style guidelines. Following these standards ensures consistency across all documentation, making it more accessible and maintainable for both human contributors and agentic LLMs.

> **Note**: This document uses domain-specific terminology. For definitions of unfamiliar terms, please refer to the [DevSynth Glossary](../glossary.md).

## Table of Contents

- [Document Structure](#document-structure)
- [Frontmatter](#frontmatter)
- [Headings and Sections](#headings-and-sections)
- [Text Formatting](#text-formatting)
- [Code Blocks](#code-blocks)
- [Links and Cross-References](#links-and-cross-references)
- [Images and Diagrams](#images-and-diagrams)
- [Tables](#tables)
- [Lists](#lists)
- [Terminology and Language](#terminology-and-language)
- [File Organization](#file-organization)
- [Review Process](#review-process)

## Document Structure

### Standard Document Template

All documentation files should follow this basic structure:

```markdown
---
title: "Document Title"
date: "YYYY-MM-DD"
version: "0.1.0-alpha.1"
tags:
  - "tag1"
  - "tag2"
status: "published"
author: "DevSynth Team"
last_reviewed: "YYYY-MM-DD"
---

# Document Title

## Executive Summary

Brief overview of the document's purpose and content.

> **Note**: This document uses domain-specific terminology. For definitions of unfamiliar terms, please refer to the [DevSynth Glossary](../glossary.md).

## Table of Contents

- [Section 1](#section-1)
- [Section 2](#section-2)

## Section 1

Content for section 1...

## Section 2

Content for section 2...

---

_Last updated: Month DD, YYYY_
```

### Document Types

Different types of documentation have specific requirements:

1. **User Guides**: Focus on how to use DevSynth, with clear step-by-step instructions and examples.
2. **Developer Guides**: Provide technical details for contributors, including architecture, code organization, and development practices.
3. **Reference Documentation**: Offer comprehensive information about APIs, commands, and configuration options.
4. **Tutorials**: Walk through specific tasks or workflows with detailed steps and explanations.
5. **Conceptual Documentation**: Explain key concepts, principles, and architectural decisions.

## Frontmatter

All Markdown files must include frontmatter with the following fields:

- `title`: The document title (should match the H1 heading)
- `date`: Creation date in YYYY-MM-DD format
- `version`: Document version (should match the project version when created)
- `tags`: Relevant keywords for categorization and search
- `status`: Document status (draft, review, published)
- `author`: Author name or team
- `last_reviewed`: Date of last review in YYYY-MM-DD format

Example:

```yaml
---
title: "DevSynth Documentation Style Guide"
date: "2025-08-02"
version: "0.1.0-alpha.1"
tags:
  - "documentation"
  - "style guide"
  - "best practices"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-02"
---
```

## Headings and Sections

### Heading Hierarchy

Use a logical heading hierarchy:

- `#` (H1): Document title (only one per document)
- `##` (H2): Major sections
- `###` (H3): Subsections
- `####` (H4): Sub-subsections
- `#####` (H5): Rarely used, only for complex documents

### Heading Style

- Use title case for H1 and H2 headings (e.g., "Document Structure")
- Use sentence case for H3 and below (e.g., "Heading hierarchy")
- Keep headings concise and descriptive
- Avoid punctuation at the end of headings
- Ensure each heading is unique within the document

## Text Formatting

### Emphasis

- Use **bold** (`**bold**`) for emphasis and UI elements
- Use *italic* (`*italic*`) for introducing new terms or for slight emphasis
- Use `code` (`` `code` ``) for code snippets, file names, and technical terms
- Avoid using underline or strikethrough for emphasis

### Paragraphs

- Keep paragraphs concise (3-5 sentences)
- Use a blank line between paragraphs
- Start each paragraph with a topic sentence
- Use transitional phrases between paragraphs for flow

### Blockquotes

Use blockquotes for:
- Notes and tips
- Important information that should stand out
- Quoting external sources

Example:

```markdown
> **Note**: This is an important note that users should pay attention to.
```

## Code Blocks

### Fenced Code Blocks

Use fenced code blocks with language specification:

````markdown
```python

def example_function():
    """Example docstring."""
    return True

```text
````

### Inline Code

Use backticks for inline code references:

```markdown
Use the `devsynth init` command to initialize a new project.
```

### Command Line Examples

For command line examples:

```markdown
```bash

# Create a new project
devsynth init --path ./my-project

```text
```

## Links and Cross-References

### Internal Links

Use relative paths for internal links:

```markdown
See the [Architecture Overview](../architecture/overview.md) for more information.
```

### External Links

For external links, include the full URL and descriptive link text:

```markdown
For more information, see the [Python documentation](https://docs.python.org/).
```

### Anchor Links

For links to sections within the same document, use anchor links:

```markdown
See the [Code Blocks](#code-blocks) section for more information.
```

### Glossary References

Include a note at the beginning of documents that use domain-specific terminology:

```markdown
> **Note**: This document uses domain-specific terminology. For definitions of unfamiliar terms, please refer to the [DevSynth Glossary](../glossary.md).
```

## Images and Diagrams

### Image Formatting

- Use descriptive file names (e.g., `architecture_diagram.png`)
- Place images in the `docs/images/` directory
- Use relative paths to reference images
- Include alt text for accessibility

Example:

```markdown
![Architecture Diagram](../images/architecture_diagram.png)
```

### Diagrams

- Use Mermaid for diagrams when possible
- Include the diagram source code in the document
- Provide a text description of the diagram for accessibility

Example:

````markdown
```mermaid

graph TD
    A[Start] --> B[Process]
    B --> C[End]

```text

The diagram shows a simple flow from Start to Process to End.
````

## Tables

### Table Formatting

Use standard Markdown tables with headers:

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |
```

### Table Headers

- Use title case for table headers
- Align columns appropriately (left for text, right for numbers)
- Keep tables simple and readable

## Lists

### Unordered Lists

Use hyphens for unordered lists:

```markdown
- Item 1
- Item 2
- Item 3
```

### Ordered Lists

Use numbers for ordered lists:

```markdown
1. First step
2. Second step
3. Third step
```

### Nested Lists

Indent nested lists with 2 or 4 spaces:

```markdown
- Main item
  - Sub-item
    - Sub-sub-item
- Another main item
```

## Terminology and Language

### Consistent Terminology

- Use terms consistently throughout the documentation
- Refer to the [DevSynth Glossary](../glossary.md) for standard definitions
- Introduce new terms in italic and define them

### Voice and Tone

- Use active voice (e.g., "Run the command" instead of "The command should be run")
- Write in a clear, concise, and professional tone
- Address the reader directly using "you" (e.g., "You can configure...")
- Use present tense when possible

### Abbreviations and Acronyms

- Define abbreviations and acronyms on first use
- Include common abbreviations in the glossary
- Use the full term followed by the abbreviation in parentheses, e.g., "Software Development Life Cycle (SDLC)"

## File Organization

### File Naming

- Use lowercase for file names
- Use underscores to separate words (e.g., `quick_start_guide.md`)
- Use descriptive names that reflect the content
- Keep file names concise

### Directory Structure

Follow the established directory structure:

- `getting_started/` – Quick start, installation, and basic usage
- `user_guides/` – User guide, CLI reference, configuration
- `developer_guides/` – Contributing, development setup, testing, code style
- `architecture/` – System, agent, memory, and reasoning architecture
- `technical_reference/` – API, error handling, performance
- `analysis/` – Project analysis, executive summary, critical recommendations
- `implementation/` – Implementation status, feature matrix, assessments
- `specifications/` – Current and archived specifications
- `roadmap/` – Roadmaps and improvement plans
- `policies/` – SDLC, security, testing, and maintenance policies

## Review Process

### Regular Reviews

- All documentation should be reviewed at least quarterly
- Update the `last_reviewed` date in the frontmatter after each review
- Update the "Last updated" date at the bottom of the document

### Review Checklist

When reviewing documentation, check for:

1. Technical accuracy
2. Completeness
3. Clarity and readability
4. Consistency with style guidelines
5. Up-to-date information
6. Working links and cross-references
7. Proper formatting

### Ownership

Each documentation file should have a designated owner responsible for keeping it up-to-date. The owner should be listed in the `author` field in the frontmatter.

## Implementation Guidelines

### For New Documentation

1. Start with the standard document template
2. Follow the style guidelines for formatting and structure
3. Include appropriate cross-references to related documents
4. Add the document to the appropriate section in the documentation index
5. Submit for review before publishing

### For Updating Existing Documentation

1. Check the `last_reviewed` date to see when it was last updated
2. Review the content for accuracy and completeness
3. Update any outdated information
4. Ensure the formatting follows the current style guidelines
5. Update the `last_reviewed` date in the frontmatter
6. Update the "Last updated" date at the bottom of the document

---

_Last updated: August 2, 2025_
