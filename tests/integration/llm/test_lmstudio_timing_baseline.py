"""LM Studio timing baseline tests.

These tests document expected response times for different payload sizes
on the development host. They are marked as slow and should be run
periodically to update timeout configurations.

Environment Context:
- Host: macOS 15.7 ARM64
- LM Studio: Running locally on localhost:1234
- Model: qwen/qwen3-4b-2507 (primary test model)
- Shared resources: Tests share host with LM Studio process
"""
import time
import pytest
import httpx
from devsynth.testing.llm_test_timeouts import TEST_TIMEOUTS

pytestmark = [
    pytest.mark.requires_resource("lmstudio"),
]


@pytest.mark.slow
def test_small_prompt_timing():
    """Verify small prompt response time (10-50 tokens).

    Measured baseline: 0.9-5.6s (avg 3s)
    Timeout: 20s (3x baseline + headroom)
    """
    endpoint = "http://localhost:1234/v1/chat/completions"
    start = time.time()

    with httpx.Client(timeout=TEST_TIMEOUTS.lmstudio_small) as client:
        response = client.post(endpoint, json={
            "model": "qwen/qwen3-4b-2507",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 20
        })

    elapsed = time.time() - start
    assert response.status_code == 200
    # Verify timeout is reasonable (3x measured baseline)
    assert elapsed < TEST_TIMEOUTS.lmstudio_small


@pytest.mark.slow
def test_medium_prompt_timing():
    """Verify medium prompt response time (100-500 tokens).

    Measured baseline: 3.7-4.8s (avg 4.5s)
    Timeout: 30s (3x baseline + headroom)
    """
    endpoint = "http://localhost:1234/v1/chat/completions"
    medium_prompt = """Analyze the following Python function and explain its time complexity:

def find_duplicates(arr):
    seen = set()
    duplicates = []
    for item in arr:
        if item in seen:
            duplicates.append(item)
        else:
            seen.add(item)
    return duplicates

Provide a detailed analysis including best case, average case, and worst case scenarios."""

    start = time.time()

    with httpx.Client(timeout=TEST_TIMEOUTS.lmstudio_medium) as client:
        response = client.post(endpoint, json={
            "model": "qwen/qwen3-4b-2507",
            "messages": [{"role": "user", "content": medium_prompt}],
            "max_tokens": 200
        })

    elapsed = time.time() - start
    assert response.status_code == 200
    assert elapsed < TEST_TIMEOUTS.lmstudio_medium


@pytest.mark.slow
def test_large_prompt_timing():
    """Verify large prompt response time (1000+ tokens).

    Measured baseline: 12.5s
    Timeout: 60s (3x baseline + headroom)
    """
    endpoint = "http://localhost:1234/v1/chat/completions"
    large_prompt = """You are an expert software architect. Review the following code and provide comprehensive feedback:

```python
class DatabaseManager:
    def __init__(self, connection_string):
        self.connection = self._create_connection(connection_string)
        self.cache = {}

    def _create_connection(self, conn_str):
        # Simplified connection creation
        return {"connected": True, "conn_str": conn_str}

    def query(self, sql, params=None):
        cache_key = (sql, tuple(params) if params else ())
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Execute query
        result = self._execute(sql, params)
        self.cache[cache_key] = result
        return result

    def _execute(self, sql, params):
        # Simplified execution
        return [{"id": 1, "name": "test"}]

    def bulk_insert(self, table, records):
        results = []
        for record in records:
            sql = f"INSERT INTO {table} VALUES ({', '.join(['?' for _ in record])})"
            results.append(self._execute(sql, record))
        return results
```

Analyze this code for:
1. Design patterns and architectural concerns
2. Performance issues and optimization opportunities
3. Security vulnerabilities
4. Testing strategies
5. Refactoring recommendations

Provide specific, actionable feedback with code examples where appropriate."""

    start = time.time()

    with httpx.Client(timeout=TEST_TIMEOUTS.lmstudio_large) as client:
        response = client.post(endpoint, json={
            "model": "qwen/qwen3-4b-2507",
            "messages": [{"role": "user", "content": large_prompt}],
            "max_tokens": 500
        })

    elapsed = time.time() - start
    assert response.status_code == 200
    assert elapsed < TEST_TIMEOUTS.lmstudio_large


@pytest.mark.fast
def test_timeout_configuration_sanity():
    """Verify that timeout configuration makes sense.

    Ensures that timeouts are ordered correctly and provide adequate headroom.
    """
    # Verify timeout ordering (small < medium < large)
    assert TEST_TIMEOUTS.lmstudio_small < TEST_TIMEOUTS.lmstudio_medium < TEST_TIMEOUTS.lmstudio_large

    # Verify health check timeout is reasonable (should be faster than small prompt)
    assert TEST_TIMEOUTS.lmstudio_health <= TEST_TIMEOUTS.lmstudio_small

    # Verify all timeouts are positive and reasonable (> 1s)
    for timeout_name in ['lmstudio_small', 'lmstudio_medium', 'lmstudio_large', 'lmstudio_health']:
        timeout_value = getattr(TEST_TIMEOUTS, timeout_name)
        assert timeout_value > 0, f"{timeout_name} should be positive"
        assert timeout_value >= 1.0, f"{timeout_name} should be at least 1s"
