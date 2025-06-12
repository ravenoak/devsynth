from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

from devsynth.logging_setup import DevSynthLogger, configure_logging

configure_logging()
logger = DevSynthLogger(__name__)

REQUEST_COUNT = Counter("request_count", "Total HTTP requests", ["endpoint"])

app = FastAPI(title="DevSynth API")

@app.middleware("http")
async def count_requests(request, call_next):
    RESPONSE = await call_next(request)
    REQUEST_COUNT.labels(endpoint=request.url.path).inc()
    return RESPONSE

@app.get("/health")
async def health() -> dict[str, str]:
    """Simple health check endpoint."""
    logger.logger.debug("Health check accessed")
    return {"status": "ok"}

@app.get("/metrics")
async def metrics() -> Response:
    """Expose Prometheus metrics."""
    data = generate_latest()
    return Response(data, media_type=CONTENT_TYPE_LATEST)
