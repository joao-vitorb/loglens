import time

from flask import Flask, Response, g, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

METRICS_PATH = "/metrics"

REQUEST_COUNT = Counter(
    "loglens_http_requests_total",
    "Total number of HTTP requests.",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "loglens_http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["method", "endpoint"],
)
LOG_ENTRIES_INGESTED = Counter(
    "loglens_log_entries_ingested_total",
    "Total number of ingested log entries.",
)
ALERTS_TRIGGERED = Counter(
    "loglens_alerts_triggered_total",
    "Total number of triggered alerts.",
)


def register_metrics(app: Flask) -> None:
    @app.before_request
    def start_timer() -> None:
        g.metrics_start = time.perf_counter()

    @app.after_request
    def record_request(response: Response) -> Response:
        if request.path == METRICS_PATH:
            return response

        endpoint = request.endpoint or "unknown"
        REQUEST_COUNT.labels(request.method, endpoint, response.status_code).inc()

        start = g.pop("metrics_start", None)
        if start is not None:
            REQUEST_LATENCY.labels(request.method, endpoint).observe(time.perf_counter() - start)
        return response

    @app.get(METRICS_PATH)
    def metrics() -> Response:
        return Response(generate_latest(), content_type=CONTENT_TYPE_LATEST)
