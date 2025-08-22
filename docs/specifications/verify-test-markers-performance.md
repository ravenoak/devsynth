# Verify Test Markers Performance

## Requirement
- The marker verification script shall skip tests requiring optional dependencies when those packages are absent (e.g., FastAPI).
- The script shall support incremental mode via `--changed` that checks only modified tests.
- Pytest collection results shall be cached in `.pytest_collection_cache.json` keyed by file hash.

## Rationale
These enhancements keep marker verification under 30s and avoid crashes from missing optional packages.
