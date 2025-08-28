"""Unit tests for individual DevSynth components.

Note:
- Do not rely on module-level speed markers. Per repository guidelines, each test
  function must declare exactly one speed marker (@pytest.mark.fast|medium|slow).
  This __init__ previously set pytestmark=[pytest.mark.fast], which is not
  recognized by our marker verification script. It has been removed to enforce
  per-function discipline.
"""

# Intentionally no module-level pytestmark here.
