"""Simple Prometheus exporter for DevSynth."""

import logging
import os
import time

from prometheus_client import Counter, start_http_server

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

REQUESTS = Counter("devsynth_exporter_requests_total", "Exporter request count")

if __name__ == "__main__":
    port = int(os.getenv("EXPORTER_PORT", "9200"))
    start_http_server(port)
    logging.info("Prometheus exporter running on port %s", port)
    while True:
        REQUESTS.inc()
        logging.info("heartbeat")
        time.sleep(5)
