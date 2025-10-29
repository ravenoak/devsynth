---

title: "Documentation Version Management"
date: "2025-06-01"
version: "0.1.0a1"
tags:
  - "policies"
  - "documentation"
  - "versioning"
  - "maintenance"

status: "published"
author: "DevSynth Team"
last_reviewed: "2025-07-10"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Policies</a> &gt; Documentation Version Management
</div>

# Documentation Version Management

## Overview

This document outlines the version management strategy for DevSynth documentation. Proper version management ensures that users can access documentation relevant to the specific version of the software they are using, while also allowing the documentation to evolve alongside the codebase.

## Version Management Strategy

DevSynth documentation uses the [mike](https://github.com/jimporter/mike) plugin for MkDocs to manage multiple versions of documentation. This approach allows:

- Maintaining documentation for multiple releases simultaneously
- Providing version-specific documentation to users
- Preserving historical documentation for reference
- Seamless navigation between different versions


## Version Naming Convention

Documentation versions follow the same versioning scheme as the software:

- **Major.Minor.Patch** (e.g., 1.0.0, 1.1.0, 2.0.0)
- **latest**: Always points to the most recent stable release
- **dev**: Points to the documentation for the current development branch


## Version Management Workflow

### Creating a New Version

When a new version of DevSynth is released:

1. Update all documentation to reflect the new version
2. Run the documentation validation checks:

   ```bash
   python scripts/validate_documentation.py
   ```

3. Deploy the new version using mike:

   ```bash
   # For a new version (e.g., 1.2.0)
   mike deploy 1.2.0

   # If this is the latest stable version
   mike deploy 1.2.0 latest --update-aliases

   # Push the changes to the gh-pages branch
   mike set-default latest --push
   ```

### Updating Existing Versions

When making changes to documentation for an existing version:

1. Check out the appropriate git branch for that version
2. Make the necessary documentation changes
3. Run the documentation validation checks
4. Deploy the updated documentation:

   ```bash
   # Update an existing version (e.g., 1.1.0)
   mike deploy 1.1.0 --update

   # Push the changes to the gh-pages branch
   mike set-default latest --push
   ```

### Development Documentation

For documentation related to unreleased features:

1. Make changes in the development branch
2. Deploy to the "dev" version:

   ```bash
   mike deploy dev --push
   ```

3. When the feature is released, incorporate the documentation into the appropriate version


## Version Archive Strategy

To manage the growth of documentation versions over time:

1. Maintain full documentation for:
   - The latest stable release
   - The previous stable release
   - The current development version
2. For older versions:
   - Archive versions older than two releases
   - Maintain a minimal set of critical documentation (installation, major features, breaking changes)
   - Include a prominent notice directing users to upgrade


## Version Switching Interface

The documentation site includes a version selector that:

1. Displays all available versions
2. Highlights the current version being viewed
3. Provides quick access to "latest" and "dev" versions
4. Maintains the user's current page when switching versions when possible


## Version-Specific Content

For content that varies between versions:

1. Use version tabs for code examples that differ between versions:

   ```markdown
   === "Version 2.x"
       ```python
       # Version 2.x code example
       ```text

   === "Version 1.x"
       ```python
       # Version 1.x code example
       ```text
   ```

2. Use admonitions to highlight version-specific features:

   ```markdown
   !!! note "Available in version 2.0+"
       This feature is only available in version 2.0 and later.
   ```

## Automation

The version management process is automated through CI/CD:

1. Documentation for new releases is automatically deployed when a release is tagged
2. The "dev" version is automatically updated when changes are merged to the development branch
3. Version validation ensures that all required documentation exists for each version


## Configuration

The mike plugin is configured in the project's `mkdocs.yml`:

```yaml
plugins:
  - mike:

      canonical_version: latest
      version_selector: true
      css_dir: css
      javascript_dir: js
```

Additional configuration is in `.github/workflows/documentation_versioning.yml` for CI/CD integration.

## Related Documents

- [Documentation Review Process](documentation_review_process.md)
- [Documentation Style Guide](documentation_style_guide.md)
- [Documentation Update Progress](../DOCUMENTATION_UPDATE_PROGRESS.md)


---
## Implementation Status

This feature is **implemented**.
