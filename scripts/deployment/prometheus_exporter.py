"""Simple Prometheus exporter for DevSynth."""

from prometheus_client import Counter, start_http_server
import time

REQUESTS = Counter("devsynth_exporter_requests_total", "Exporter request count")

if __name__ == "__main__":
    start_http_server(9200)
    while True:
        REQUESTS.inc()
        time.sleep(5)


