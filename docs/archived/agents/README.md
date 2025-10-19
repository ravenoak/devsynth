# AGENTS.md Consolidation Archive

This directory contains archived AGENTS.md files that were consolidated as part of the Documentation Harmonization project (September 30, 2025).

## Consolidation Rationale

Multiple AGENTS.md files created maintenance burden and potential inconsistency. The consolidation establishes a single source of truth while preserving historical content.

## File Mappings

| Original Location | Archived As | Status | Notes |
|------------------|-------------|---------|-------|
| `/AGENTS.md` | *Not archived* | **Canonical** | Single source of truth |
| `docs/AGENTS.md` | *Removed* | Deprecated | Was pointer to root version |
| `src/AGENTS.md` | `src-AGENTS-20250930.md` | Archived | Source-specific guidance integrated into root |
| `tests/AGENTS.md` | `tests-AGENTS-20250930.md` | Archived | Test-specific guidance integrated into root |
| `docs/archived/AGENTS.md` | *Unchanged* | Historical | Pre-existing archived version |

## Canonical Source

**Current canonical location**: `/AGENTS.md`

All directory-specific guidance from archived files has been integrated into the root AGENTS.md to maintain comprehensive coverage while eliminating duplication.

## Integration Summary

The root AGENTS.md now includes:
- General project setup and conventions (original content)
- Source code development guidance (from `src/AGENTS.md`)
- Testing procedures and conventions (from `tests/AGENTS.md`)
- Documentation editing guidelines (from archived `docs/AGENTS.md`)

## Access to Archived Content

The archived files in this directory preserve the complete historical content for reference purposes. They should not be used for current development guidance.

---

*Created: September 30, 2025*
*Part of: Documentation Harmonization Phase 1*
