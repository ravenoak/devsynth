---

author: Author Name
date: YYYY-MM-DD
last_reviewed: "2025-07-10"
status: draft
tags:

- tag1
- tag2
- relevant_keyword

title: Document Title
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; Document Title
</div>

# Document Title

This document serves as a template and guide for the front-matter metadata to be included at the beginning of every Markdown file in the DevSynth project. Consistent metadata is crucial for documentation management, versioning, searchability, and for tools like DevSynth to ingest and analyze project artifacts.

## Field Explanations:

- **`title`**: (String, Required)
    *   The main title of the document.
    *   Example: `"DevSynth Architecture Overview"`

*   **`date`**: (String, Required)
    *   The original publication date or last significant update date of the document content.
    *   Format: `YYYY-MM-DD` (e.g., `"2024-05-20"`) or full ISO 8601 timestamp (e.g., `"2024-05-20T14:30:00Z"`).

*   **`version`**: (String, Required)
    *   The semantic version of this specific document (e.g., "1.0.0", "1.0.1-alpha"). This helps track changes to the document itself, independently of project versions if necessary.
    *   Example: `"1.1.0"`

*   **`tags`**: (List of Strings, Required)
    *   A list of relevant keywords or tags that help categorize and find the document.
    *   Example: `["architecture", "planning", "database"]`

*   **`status`**: (String, Required)
    *   The current status of the document.
    *   Allowed values:
        *   `"draft"`: The document is still in progress and not yet ready for general review or use.
        *   `"review"`: The document is ready for review by stakeholders.
        *   `"published"`: The document is considered stable and officially published.
        *   `"archived"`: The document is outdated or no longer relevant and has been archived.
    *   Example: `"published"`

*   **`author`**: (String, Optional)
    *   The name or alias of the primary author or current maintainer of the document.
    *   Example: `"Jane Doe"`

*   **`last_reviewed`**: (String, Optional)
    *   The date when the document was last reviewed for accuracy and relevance.
    *   Format: `YYYY-MM-DD`
    *   Example: `"2025-01-15"`


## Usage:

Copy the `---` delimited block at the top of this template into the beginning of your Markdown file and fill in the appropriate values. The `devsynth validate-metadata` command will be used in CI to ensure all documents adhere to this schema.
## Implementation Status

.
