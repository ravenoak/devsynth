from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.responses import Response
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

from devsynth.logging_setup import DevSynthLogger, configure_logging
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

app = FastAPI(title="DevSynth API")


@app.middleware("http")
async def count_requests(request, call_next):
    RESPONSE = await call_next(request)
    REQUEST_COUNT.labels(endpoint=request.url.path).inc()
    return RESPONSE


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
