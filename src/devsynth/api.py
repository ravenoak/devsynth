from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable, Sequence
from typing import Protocol, TypedDict, TypeVar, cast

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import Response

from devsynth.interface.agentapi import router as agent_router


class CounterMetric(Protocol):
    def labels(self, *, endpoint: str) -> CounterMetric: ...

    def inc(self) -> None: ...


class HistogramMetric(Protocol):
    def labels(self, *, endpoint: str) -> HistogramMetric: ...

    def observe(self, amount: float) -> None: ...


CounterFactory = Callable[[str, str, Sequence[str]], CounterMetric]
HistogramFactory = Callable[[str, str, Sequence[str]], HistogramMetric]


# Prometheus metrics are optional; fall back to lightweight stubs when the
# dependency isn't available.  This keeps the API usable in stripped-down test
# environments where the monitoring stack is absent.
try:  # pragma: no cover - import guarded for optional dependency
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
    )
    from prometheus_client import Counter as _PrometheusCounter
    from prometheus_client import Histogram as _PrometheusHistogram
    from prometheus_client import (
        generate_latest,
    )

    counter_factory: CounterFactory = _PrometheusCounter
    histogram_factory: HistogramFactory = _PrometheusHistogram
except ImportError:  # pragma: no cover - fallback for minimal environments

    class _NoopMetric:
        def __init__(self, *args: object, **kwargs: object) -> None:  # noqa: D401
            pass

        def labels(self, *args: object, **kwargs: object) -> _NoopMetric:
            return self

        def inc(self, *args: object, **kwargs: object) -> None:
            pass

        def observe(self, *args: object, **kwargs: object) -> None:
            pass

        def clear(self) -> None:
            pass

    def counter_factory(*args: object, **kwargs: object) -> CounterMetric:
        return _NoopMetric()

    def histogram_factory(*args: object, **kwargs: object) -> HistogramMetric:
        return _NoopMetric()

    def generate_latest(registry: object | None = None) -> bytes:
        return b""

    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"

import time

from devsynth.config.settings import get_settings
from devsynth.logger import clear_request_context, set_request_context, setup_logging

logger = setup_logging(__name__)
settings = get_settings()


class HealthResponse(TypedDict):
    status: str


def verify_token(authorization: str | None = Header(None)) -> None:
    """Verify Bearer token from Authorization header if access control enabled."""
    token = settings.access_token
    if token and authorization != f"Bearer {token}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )


REQUEST_COUNT: CounterMetric = counter_factory(
    "request_count", "Total HTTP requests", ["endpoint"]
)
REQUEST_LATENCY: HistogramMetric = histogram_factory(
    "request_latency_seconds",
    "HTTP request latency",
    ["endpoint"],
)

app: FastAPI = FastAPI(title="DevSynth API")

AsyncEndpoint = TypeVar("AsyncEndpoint", bound=Callable[..., Awaitable[object]])

# Expose workflow endpoints under the `/api` namespace.
app.include_router(agent_router, prefix="/api")


http_middleware = cast(Callable[[AsyncEndpoint], AsyncEndpoint], app.middleware("http"))


@http_middleware
async def request_context_and_metrics(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
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


health_route = cast(
    Callable[[AsyncEndpoint], AsyncEndpoint],
    app.get("/health"),
)


@health_route
async def health(token: None = Depends(verify_token)) -> HealthResponse:
    """Simple health check endpoint."""
    logger.logger.debug("Health check accessed")
    return {"status": "ok"}


metrics_route = cast(
    Callable[[AsyncEndpoint], AsyncEndpoint],
    app.get("/metrics"),
)


@metrics_route
async def metrics(token: None = Depends(verify_token)) -> Response:
    """Expose Prometheus metrics."""
    data = generate_latest()
    return Response(data, media_type=CONTENT_TYPE_LATEST)
