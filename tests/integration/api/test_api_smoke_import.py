import os

import pytest


@pytest.mark.medium
def test_fastapi_api_import_smoke():
    """Minimal smoke test for API server import under the api extra.

    - Skips if FastAPI is not installed (api extra not enabled).
    - Verifies the app object can be imported and basic metrics exports are defined.

    ReqID: API-SMOKE-IMPORT
    """
    fastapi = pytest.importorskip("fastapi")

    # Allow opt-out via resource flag for environments without extras
    if os.getenv("DEVSYNTH_RESOURCE_API_AVAILABLE", "true").lower() not in {
        "1",
        "true",
        "yes",
    }:
        pytest.skip("API resource not enabled in this environment")

    # Import the lightweight API module and perform basic checks
    import devsynth.api as api

    assert hasattr(api, "app"), "FastAPI app should be defined"
    assert isinstance(api.app, fastapi.FastAPI)

    # Prometheus exports should be present even when prometheus_client isn't installed
    assert hasattr(api, "CONTENT_TYPE_LATEST")
    assert hasattr(api, "generate_latest")
    assert callable(api.generate_latest)
