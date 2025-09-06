import uuid

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.responses import Response

from devsynth.interface.agentapi import router as agent_router

# Prometheus metrics are optional; fall back to lightweight stubs when the
# dependency isn't available.  This keeps the API usable in stripped-down test
# environments where the monitoring stack is absent.
try:  # pragma: no cover - import guarded for optional dependency
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        Counter,
        Histogram,
        generate_latest,
    )
except ImportError:  # pragma: no cover - fallback for minimal environments

    class _NoopMetric:
        def __init__(self, *args: object, **kwargs: object) -> None:  # noqa: D401
            pass

        def labels(self, *args: object, **kwargs: object) -> "_NoopMetric":
            return self

        def inc(self, *args: object, **kwargs: object) -> None:
            pass

        def observe(self, *args: object, **kwargs: object) -> None:
            pass

        def clear(self) -> None:
            pass

    Counter = Histogram = _NoopMetric

    # Match prometheus_client.generate_latest signature to avoid overrides
    # def generate_latest(registry: CollectorRegistry = ...) -> bytes
    def generate_latest(registry: object | None = None) -> bytes:
        return b""

    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"

import time
from typing import Union

from devsynth.config.settings import get_settings
from devsynth.logger import clear_request_context, set_request_context, setup_logging

logger = setup_logging(__name__)
settings = get_settings()


def verify_token(authorization: Union[str, None] = Header(None)) -> None:
    """Verify Bearer token from Authorization header if access control enabled."""
    token = settings.access_token
    if token and authorization != f"Bearer {token}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )


REQUEST_COUNT = Counter("request_count", "Total HTTP requests", ["endpoint"])
REQUEST_LATENCY = Histogram(
    "request_latency_seconds",
    "HTTP request latency",
    ["endpoint"],
)

app = FastAPI(title="DevSynth API")

# Expose workflow endpoints under the `/api` namespace.
app.include_router(agent_router, prefix="/api")


@app.middleware("http")
async def request_context_and_metrics(request, call_next):
    """Attach correlation ID and record metrics in a single middleware."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    set_request_context(request_id=request_id)
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    endpoint = request.url.path
    REQUEST_COUNT.labels(endpoint=endpoint).inc()
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
    response.headers["X-Request-ID"] = request_id
    clear_request_context()
    return response


@app.get("/health")
async def health(token: None = Depends(verify_token)) -> dict[str, str]:
    """Simple health check endpoint."""
    logger.logger.debug("Health check accessed")
    return {"status": "ok"}


@app.get("/metrics")
async def metrics(token: None = Depends(verify_token)) -> Response:
    """Expose Prometheus metrics."""
    data = generate_latest()
    return Response(data, media_type=CONTENT_TYPE_LATEST)
