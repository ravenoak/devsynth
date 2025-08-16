# Issue 113: Kuzu memory integration errors
Milestone: 0.1.0-alpha.1 (completed 2025-08-14)

The Kuzu backed memory store fails during test setup:
```
AttributeError: module 'devsynth.config.settings' has no attribute 'kuzu_embedded'
```
Tests affected include [`tests/integration/general/test_kuzu_memory_integration.py`](../tests/integration/general/test_kuzu_memory_integration.py) and unit adapter tests. Fix the configuration lookup and ensure ephemeral stores initialise correctly.

## Progress
- [`tests/integration/general/test_kuzu_memory_integration.py`](../tests/integration/general/test_kuzu_memory_integration.py) now passes.
- Configuration lookup corrected and ephemeral stores initialise properly.
- Fixed in [4e7115ef](../commit/4e7115ef).
- Status: closed — 2025-08-14
