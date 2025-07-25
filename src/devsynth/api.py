from fastapi import FastAPI, Depends, HTTPException, status, Header
import uuid
from fastapi.responses import Response
from prometheus_client import (
    Counter,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
import time

from devsynth.logging_setup import (
    DevSynthLogger,
    configure_logging,
    set_request_context,
    clear_request_context,
)
from devsynth.config.settings import get_settings

configure_logging()
logger = DevSynthLogger(__name__)
settings = get_settings()


def verify_token(authorization: str | None = Header(None)) -> None:
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


@app.middleware("http")
async def add_request_id(request, call_next):
    """Attach a correlation ID to each request and log context."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    set_request_context(request_id=request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    clear_request_context()
    return response


@app.middleware("http")
async def count_requests(request, call_next):
    RESPONSE = await call_next(request)
    REQUEST_COUNT.labels(endpoint=request.url.path).inc()
    return RESPONSE


@app.middleware("http")
async def record_latency(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    REQUEST_LATENCY.labels(endpoint=request.url.path).observe(duration)
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
