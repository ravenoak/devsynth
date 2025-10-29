---

author: DevSynth Team
date: '2025-07-07'
last_reviewed: "2025-07-10"
status: published
tags:

- policy
- guide

title: DevSynth Documentation Style Guide
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Policies</a> &gt; DevSynth Documentation Style Guide
</div>

# DevSynth Documentation Style Guide

## Overview

This style guide establishes standards for all DevSynth documentation to ensure consistency, clarity, and usability. It applies to all markdown files in the project, including README files, user guides, developer documentation, and technical references.

## Document Structure

### Frontmatter

All documentation files should include YAML frontmatter with the following fields:

```yaml
---
title: "Document Title"
date: "YYYY-MM-DD" # Date of creation
version: "0.1.0a1"
tags:
  - "tag1"
  - "tag2"

status: "draft|review|published"
author: "Author Name or DevSynth Team"
last_reviewed: "YYYY-MM-DD" # Date of last review
---
```

### Heading Hierarchy

- Use a single H1 (`#`) for the document title
- Use H2 (`##`) for major sections
- Use H3 (`###`) for subsections
- Use H4 (`####`) for sub-subsections
- Avoid skipping heading levels (e.g., don't go from H2 to H4)
- Keep headings concise and descriptive


### Document Sections

Standard documents should include the following sections when applicable:

1. **Overview/Introduction** - Brief explanation of the document's purpose
2. **Main Content** - Organized into logical sections with clear headings
3. **Related Documents** - Links to related documentation
4. **References** - Citations or external resources
5. **Changelog** - Document revision history (for major documents)


## Writing Style

### Voice and Tone

- Use active voice rather than passive voice
- Write in a clear, concise, and professional tone
- Use present tense when possible
- Address the reader directly using "you" rather than "the user"
- Use gender-neutral language


### Formatting

- Use **bold** for emphasis and UI elements
- Use *italics* for introducing new terms or for slight emphasis
- Use `code formatting` for code snippets, file names, and technical terms
- Use blockquotes for important notes or quotes


### Lists

- Use ordered lists (1., 2., 3.) for sequential steps or prioritized items
- Use unordered lists (bullet points) for non-sequential items
- Be consistent with punctuation in lists (either all items end with periods or none do)
- Keep list items parallel in structure


## Code Examples

### Inline Code

Use backticks for inline code references:

```markdown
Use the `devsynth init` command to initialize a new project.
```

### Code Blocks

Use fenced code blocks with language specification for syntax highlighting:

````markdown
```python

def example_function():
    """This is an example function."""
    return "Hello, world!"

```text
````

### Command Line Examples

For command line examples, use the `bash` or `shell` language specifier:

````markdown
```bash

# Initialize a new project

devsynth init --path ./my-project

```text
````

## Links and References

### Internal Links

Use relative links for internal documentation:

```markdown
See the [Installation Guide](../getting_started/installation.md) for more information.
```

### External Links

Use descriptive link text for external links:

```markdown
Read more about Python in the [official Python documentation](https://docs.python.org/).
```

### Cross-References

Add a "Related Documents" section at the end of each document:

```markdown

## Related Documents

- [User Guide](../user_guides/user_guide.md) - Comprehensive guide for users
- [API Reference](../technical_reference/api_reference/index.md) - Detailed API documentation

```

## Admonitions and Callouts

Use admonitions for important information:

```markdown
!!! note
    This is a note that provides additional information.

!!! warning
    This is a warning that alerts the user to potential issues.

!!! tip
    This is a tip that provides helpful advice.
```

## Images and Diagrams

- Include descriptive alt text for all images
- Use SVG format for diagrams when possible
- Keep image file sizes reasonable
- Place images in an `assets` or `images` directory
- Use consistent naming conventions for image files


```markdown
![Class diagram showing the relationship between components](../assets/class_diagram.svg)
```

## Tables

Use tables for structured data:

```markdown
| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |
```

## Terminology

- Use consistent terminology throughout all documentation
- Define technical terms in a glossary
- Avoid jargon and acronyms without explanation
- When using acronyms, spell them out on first use


## File Organization

- Place documentation files in the appropriate directory based on content type
- Use lowercase file names with hyphens for spaces (e.g., `user-guide.md`)
- Include an `index.md` file in each directory to provide an overview
- Follow the directory structure defined in the documentation plan


## Review and Maintenance

- Review documentation regularly for accuracy and relevance
- Update the `last_reviewed` date in the frontmatter when reviewing
- Increment the version number for significant changes
- Add entries to the document changelog for major updates


## Accessibility

- Use descriptive link text (avoid "click here" or "read more")
- Provide alt text for all images
- Use sufficient color contrast
- Structure content with proper headings for screen readers
- Avoid relying solely on color to convey information


## Versioning

- Include version information in the frontmatter
- Clearly mark version-specific content
- Use semantic versioning (MAJOR.MINOR.PATCH) for document versions
- Archive outdated documentation rather than deleting it


## Implementation Examples

### Example Document Structure

```markdown
---
title: "Feature X User Guide"
date: "2025-06-01"
version: "0.1.0a1"
tags:
  - "feature-x"
  - "user-guide"

status: "published"
author: "DevSynth Team"
last_reviewed: "2025-06-15"
---

# Feature X User Guide

## Overview

This guide explains how to use Feature X in DevSynth.

## Prerequisites

Before using Feature X, ensure you have:

- DevSynth version 1.2.0 or higher
- Python 3.12 or higher
- Required dependencies installed


## Basic Usage

To use Feature X:

1. Initialize Feature X with `devsynth feature-x init`
2. Configure settings in the configuration file
3. Run Feature X with `devsynth feature-x run`


## Advanced Configuration

### Custom Templates

You can use custom templates by...

## Troubleshooting

### Common Issues

If you encounter error XYZ, try...

## Related Documents

- [Feature X API Reference](../technical_reference/api_reference/feature_x.md)
- [Feature X Architecture](../architecture/feature_x.md)


## Changelog

- **1.0.0** (2025-06-01): Initial version
- **1.0.1** (2025-06-15): Added troubleshooting section

```

## Implementation Status

This feature is **implemented**.
