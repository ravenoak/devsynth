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

## LLM Provider API Key Requirements

### Current API Key Status

**Anthropic API**: Currently waiting on valid API key for testing. Tests requiring Anthropic API are expected to fail until key is available.

**OpenAI API**: Valid API keys available. Use only cheap, inexpensive models (e.g., gpt-3.5-turbo, gpt-4o-mini) and only when absolutely necessary for testing core functionality.

**OpenRouter API**: Valid API keys available with free-tier access. Use OpenRouter free-tier for:
- All OpenRouter-specific tests
- General tests requiring live LLM functionality
- Prefer OpenRouter over OpenAI for cost efficiency

**LM Studio**: Tests run on same host as application tests. Resources are limited - use large timeouts (60+ seconds) and consider resource constraints when designing tests.

### Testing Strategy

1. **Primary LLM Provider**: Use OpenRouter free-tier for all tests requiring live LLM functionality
2. **Fallback Providers**: Use only when OpenRouter is unavailable or for provider-specific testing
3. **Cost Optimization**: Minimize API calls, use smallest/cheapest models available
4. **Resource Awareness**: LM Studio tests share host resources - design for reliability over speed

### Environment Variables

Set the following environment variables for LLM provider testing:

```bash
# OpenRouter (preferred for testing)
export OPENROUTER_API_KEY="your-openrouter-key"
export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"

# OpenAI (use sparingly, only cheap models)
export OPENAI_API_KEY="your-openai-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"

# LM Studio (local testing)
export LM_STUDIO_ENDPOINT="http://127.0.0.1:1234"
export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE="true"
```

### Test Markers

Use appropriate markers for LLM provider tests:

```python
@pytest.mark.requires_resource("openrouter")  # For OpenRouter-specific tests
@pytest.mark.requires_resource("openai")      # For OpenAI-specific tests
@pytest.mark.requires_resource("lmstudio")    # For LM Studio tests
@pytest.mark.slow                             # For tests requiring LLM API calls
```

## LM Studio Timeout Configuration

LM Studio tests run on the same host as the application, sharing system resources. This requires conservative timeout settings to account for system load and variable response times.

### Baseline Performance Measurements

**Environment Context:**
- Host: macOS 15.7 ARM64
- LM Studio: Running locally on localhost:1234
- Model: qwen/qwen3-4b-2507 (primary test model)
- Shared resources: Tests share host with LM Studio process

**Measured Response Times:**
- **Small prompts (10-50 tokens):** 0.9s - 5.6s (avg ~3s)
- **Medium prompts (100-500 tokens):** 3.7s - 4.8s (avg ~4.5s)
- **Large prompts (1000+ tokens):** 12.5s measured

### Timeout Configuration Strategy

Timeouts are set to **2-3x measured baseline** to provide adequate headroom for:
- System load variations
- Concurrent test execution
- CI environment differences

**Default Timeouts:**
- Small prompts: **20 seconds**
- Medium prompts: **30 seconds**
- Large prompts: **60 seconds**
- Health checks: **10 seconds**

### Environment Variable Overrides

Customize timeouts for different environments using these variables:

```bash
# LM Studio timeouts (seconds)
export DEVSYNTH_TEST_TIMEOUT_LMSTUDIO_SMALL=20.0
export DEVSYNTH_TEST_TIMEOUT_LMSTUDIO_MEDIUM=30.0
export DEVSYNTH_TEST_TIMEOUT_LMSTUDIO_LARGE=60.0
export DEVSYNTH_TEST_TIMEOUT_LMSTUDIO_HEALTH=10.0

# OpenAI/OpenRouter timeouts (faster, cloud-based)
export DEVSYNTH_TEST_TIMEOUT_OPENAI_SMALL=10.0
export DEVSYNTH_TEST_TIMEOUT_OPENAI_MEDIUM=15.0
export DEVSYNTH_TEST_TIMEOUT_OPENAI_LARGE=30.0

# Generic timeouts
export DEVSYNTH_TEST_TIMEOUT_GENERIC=30.0
export DEVSYNTH_TEST_TIMEOUT_STREAMING=60.0
```

### Troubleshooting Timeout Issues

**Tests timing out frequently:**
1. Increase timeout values using environment variables above
2. Check system load (`top`, `htop`) during test runs
3. Consider running tests serially (`--no-parallel`) if resource contention is high
4. Monitor LM Studio logs for performance issues

**Tests too slow in CI:**
1. Use more generous timeouts in CI environment
2. Consider skipping LM Studio tests in CI (`export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=false`)
3. Run timing baseline tests periodically to recalibrate timeouts

**Re-measuring baselines:**
1. Run `tests/integration/llm/test_lmstudio_timing_baseline.py` with LM Studio running
2. Update timeout configuration based on new measurements
3. Document any significant changes in environment or performance
