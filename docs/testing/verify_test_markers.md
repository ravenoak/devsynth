# Verifying test markers

DevSynth enforces speed markers on tests to keep runtimes predictable. The CI
workflow runs `poetry run python scripts/verify_test_markers.py --report
--cross-check-collection` to ensure each test is marked appropriately and that
runtime collection agrees with the static scan.

Key rules:

- Exactly one speed marker per test: `fast`, `medium`, or `slow`.
- Prefer function-level decorators. Module-level `pytestmark =
  [pytest.mark.fast]` (or `medium`/`slow`) is acceptable when all tests in the
  module share the same speed profile.
- Parametrized tests may attach the speed marker to each `pytest.param` entry,
  but the effective marker across all parameters must still be identical.
- Property tests require a speed marker in addition to
  `@pytest.mark.property`.

Examples

Correct (function-level):
```python
import pytest

@pytest.mark.fast
def test_addition():
    assert 1 + 2 == 3
```

Correct (module-level when all tests in the file share the same speed):
```python
import pytest

pytestmark = [pytest.mark.medium]

def test_addition():
    assert 1 + 2 == 3
```

## Custom markers

Project-specific markers must be documented so automation can verify they
exist. The verification script reads the configured markers from
`pyproject.toml` and `tests/conftest_extensions.py` and emits warnings when it
encounters unregistered names. If you have a legitimate use-case for a new
marker:

1. Add an entry under `[tool.pytest.ini_options].markers` in `pyproject.toml`.
   Use the format `"marker_name: concise description"`.
2. Update `tests/conftest_extensions.py` so the `pytest_configure` hook
   registers the marker and, if necessary, documents any special handling for
   ad-hoc markers.
3. Extend this document with the rationale and remediation guidance.
4. Re-run `poetry run python scripts/verify_test_markers.py --report
   --cross-check-collection` to ensure `files_with_issues` remains `0`.

The repository currently defines the `integtest` marker for legacy
integration-provider smoke tests. Combine it with a speed marker and the
appropriate `requires_resource("<name>")` guard when maintaining those tests.

## Local usage

Run the verification script before committing new or updated tests. The
`--cross-check-collection` flag surfaces mismatches between static analysis and
pytest's view of the suite, while `--report` refreshes
`test_reports/test_markers_report.json`.

```bash
poetry run python scripts/verify_test_markers.py --report --cross-check-collection
```

For faster iteration on modified files:
```bash
poetry run python scripts/verify_test_markers.py --changed
```

Generate a JSON report (saved as test_markers_report.json):
```bash
poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json
```

When the verifier emits warnings about "ad-hoc" markers, either replace the
marker with a standardized alternative or follow the registration process above
so the automation understands it. The runtime plugin in
`tests/conftest_extensions.py` will continue to warn on unregistered markers to
prevent silent drift.
