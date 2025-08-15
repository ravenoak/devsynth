"""Simple Prometheus exporter for DevSynth."""

import logging
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from prometheus_client import Counter, start_http_server

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def _ensure_non_root() -> None:
    if os.geteuid() == 0:
        sys.stderr.write("Please run this script as a non-root user.\n")
        raise SystemExit(1)


def _load_env() -> None:
    env_path = Path(".env")
    if env_path.exists():
        if env_path.stat().st_mode & 0o777 != 0o600:
            raise RuntimeError(f"Environment file {env_path} must have 600 permissions")
        load_dotenv(env_path)


REQUESTS = Counter("devsynth_exporter_requests_total", "Exporter request count")

if __name__ == "__main__":
    _ensure_non_root()
    _load_env()
    port = int(os.getenv("EXPORTER_PORT", "9200"))
    start_http_server(port)
    logging.info("Prometheus exporter running on port %s", port)
    while True:
        REQUESTS.inc()
        logging.info("heartbeat")
        time.sleep(5)
