# Optional Services and Backend Test Gating

This guide documents the pytest helpers for optional backends so developers can
collect or run backend-focused suites without brittle import errors. It
complements the [integration extras guide](integration_extras.md) with concrete
fixture usage, environment flags, and Poetry commands.

## Fixtures and helpers

`tests/fixtures/resources.py` exposes the following utilities (each helper relies on
`importlib.util.find_spec` so missing modules surface as clean skips instead of
`ImportError`s during collection):

- `skip_if_missing_backend(resource, *, extras=None, import_names=None)` – returns
  markers (including `requires_resource(resource)`) that skip tests when the
  corresponding `DEVSYNTH_RESOURCE_<NAME>_AVAILABLE` flag is false or the
  backend package is absent. Apply it in `pytestmark` lists or parametrized
  `pytest.param` blocks.
- `backend_param(*values, resource=...)` – wraps `pytest.param` with the same
  skip/marker logic for parametrized tests, ensuring each case keeps the
  resource marker. Use it when a single test covers multiple optional services.
- `backend_import_reason(resource)` – returns a clear reason string for
  `pytest.importorskip`, pointing to the Poetry extras that install the backend.

Example module-level usage:

```python
from tests.fixtures.resources import backend_import_reason, skip_if_missing_backend

pytestmark = [
    *skip_if_missing_backend("chromadb"),
    pytest.mark.medium,
]

chromadb = pytest.importorskip(
    "chromadb",
    reason=backend_import_reason("chromadb"),
)
```

Always prefer `pytest.importorskip` for optional imports—including the internal
DevSynth adapters—so the module either loads successfully or exits early with
the same resource-aware skip message emitted by the fixtures above.

For parametrized smoke tests:

```python
from tests.fixtures.resources import backend_import_reason, backend_param

BACKENDS = [
    backend_param("chromadb", resource="chromadb"),
    backend_param("faiss", resource="faiss"),
]

@pytest.mark.fast
@pytest.mark.parametrize("module_name", BACKENDS)
def test_optional_backend(module_name: str) -> None:
    pytest.importorskip(module_name, reason=backend_import_reason(module_name))
```

## Environment flags

Each optional backend responds to a dedicated environment flag. Set the flag to
`true` (case-insensitive) to opt into the tests once dependencies are installed,
or to `false` to force a skip.

| Resource | Flag | Notes |
| --- | --- | --- |
| `chromadb` | `DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE` | defaults to `true`; helper prints install hints |
| `faiss` | `DEVSYNTH_RESOURCE_FAISS_AVAILABLE` | defaults to `true` |
| `kuzu` | `DEVSYNTH_RESOURCE_KUZU_AVAILABLE` | defaults to `true` |
| `lmdb` | `DEVSYNTH_RESOURCE_LMDB_AVAILABLE` | defaults to `true` |
| `tinydb` | `DEVSYNTH_RESOURCE_TINYDB_AVAILABLE` | defaults to `true` |
| `duckdb` | `DEVSYNTH_RESOURCE_DUCKDB_AVAILABLE` | defaults to `true` |
| `rdflib` | `DEVSYNTH_RESOURCE_RDFLIB_AVAILABLE` | defaults to `true` |

When a flag is explicitly `false`, `skip_if_missing_backend` adds a consistent
skip message reminding contributors to re-enable the flag after installing the
packages.

## Poetry extras

Install the corresponding extras before opting into backend suites:

- `poetry install --extras retrieval` → installs `kuzu` and `faiss-cpu`.
- `poetry install --extras chromadb` → installs `chromadb` and `tiktoken`.
- `poetry install --extras memory` → installs `tinydb`, `duckdb`, `lmdb`,
  `kuzu`, `faiss-cpu`, `chromadb`, and supporting dependencies.
- `poetry install --extras tests` → installs the lightweight adapters (`lmdb`,
  `duckdb`, `tinydb`) required by unit fixtures.

Use the smallest extra that satisfies your target backend to keep installs
lightweight. The helpers automatically mention the relevant extras when a
dependency is missing.

## Targeted collection

The backend smoke suite lives under `tests/backend_subset/` and depends on the
fixtures above. To verify skips in environments without optional dependencies:

```bash
poetry run pytest tests/backend_subset --collect-only
```

Collection should succeed with informative skips instead of import errors. Once
you install the extras and export the resource flags, rerun without
`--collect-only` to execute the backend checks.
