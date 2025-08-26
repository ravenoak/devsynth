# Verifying test markers

DevSynth enforces speed markers on tests to keep runtimes predictable. The CI workflow
runs `poetry run python scripts/verify_test_markers.py` to ensure each test is
marked appropriately.

Key rules:
- Exactly one speed marker per test function: `@pytest.mark.fast` OR `@pytest.mark.medium` OR `@pytest.mark.slow`.
- Do not use module-level `pytestmark` for speed categories; apply at the function level.
- Parametrized tests: Prefer a single function-level speed marker. Alternatively, if you use `pytest.param(..., marks=pytest.mark.<speed>)`, every parameter must specify exactly one identical speed marker; mixed or missing markers will be flagged.
- Property tests require a speed marker in addition to `@pytest.mark.property`.

Examples

Correct:
```python
import pytest

@pytest.mark.fast
def test_addition():
    assert 1 + 2 == 3
```

Incorrect (module-level speed marker; will be flagged):
```python
import pytest

pytestmark = pytest.mark.fast

def test_addition():
    assert 1 + 2 == 3
```

## Local usage

Run the verification script before committing new or updated tests:

```bash
poetry run python scripts/verify_test_markers.py
```

For faster iteration on modified files:
```bash
poetry run python scripts/verify_test_markers.py --changed
```

Generate a JSON report (saved as test_markers_report.json):
```bash
poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json
```
