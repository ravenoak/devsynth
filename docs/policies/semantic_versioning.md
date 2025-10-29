---

title: "Semantic Versioning Policy"
date: "2025-07-07"
version: "0.1.0a1"
tags:
  - "policy"
  - "versioning"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-07-10"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Policies</a> &gt; Semantic Versioning Policy
</div>

# Semantic Versioning Policy

DevSynth follows the [Semantic Versioning](https://semver.org/) scheme to communicate changes and compatibility.

## Version Components

- **MAJOR** version when incompatible API changes are introduced.
- **MINOR** version when functionality is added in a backward compatible manner.
- **PATCH** version for backward compatible bug fixes.

## Pre-release Identifiers

Pre-release versions append an identifier after a hyphen (e.g., `1.2.0-alpha`,
`2.0.0-rc.1`) to denote milestones that precede a final release.

## MAJOR.MINOR.PATCH-STABILITY

DevSynth uses an extended scheme that appends a stability label after the patch
component. The full version string is `MAJOR.MINOR.PATCH-STABILITY`.

- **STABILITY** indicates the maturity of the release. Typical values are
  `alpha`, `beta`, and `rc` followed by a dot and an incrementing number.
  - Final releases omit the stability label entirely.

### Examples

- `0.1.0-alpha.1` – first alpha iteration of version `0.1.0`.
- `0.1.0-rc.1` – first release candidate of version `0.1.0`.

## Semantic Versioning+

To clarify milestone quality and communicate expectations during the long pre-1.0 period, DevSynth introduces **Semantic Versioning+ (SemVer+)**. The scheme
extends the standard `MAJOR.MINOR.PATCH` format with an optional stability
segment and a plus sign for build metadata. The overall pattern is:

```text
MAJOR.MINOR.PATCH[-STABILITY][+BUILD]
```

- **STABILITY** (`alpha`, `beta`, `rc`) conveys the level of confidence in a
  release. An incrementing number (e.g., `alpha.2`) denotes successive previews.
- **BUILD** is optional metadata such as commit hashes or packaging notes. It
  follows the plus sign defined in the SemVer specification.

SemVer+ is fully compatible with Semantic Versioning and tooling that expects
`MAJOR.MINOR.PATCH`. The stability label simply provides clearer guidance for
users evaluating whether a release is experimental or production ready. Build
metadata is ignored when determining upgrade paths, but helps trace artifacts.

### Practical Guidelines

1. Start new feature lines at `alpha.1` and increment through `beta` and `rc`
   as quality improves.
2. Omit the stability label once a release is considered stable.
3. Use `+<build>` metadata for internal automation or distribution channels.

With Semantic Versioning+ in place, version strings like `0.3.0-beta.2+exp.sha`
communicate both the development phase and the specific build artifact.
## Implementation Status

This feature is **implemented**.
