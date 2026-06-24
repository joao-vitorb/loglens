from flask.testing import FlaskClient


def test_metrics_endpoint_is_public_and_exposes_prometheus_text(client: FlaskClient) -> None:
    response = client.get("/metrics")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "text/plain" in response.content_type
    assert "loglens_http_requests_total" in body
    assert "loglens_http_request_duration_seconds" in body


def test_metrics_count_ingested_log_entries(client: FlaskClient) -> None:
    payload = {
        "entries": [
            {
                "timestamp": "2026-06-20T08:00:00",
                "level": "info",
                "source": "svc",
                "message": "ok",
            }
        ]
    }
    client.post("/api/v1/logs", json=payload)

    body = client.get("/metrics").get_data(as_text=True)

    assert "loglens_log_entries_ingested_total" in body


def test_metrics_record_http_requests(client: FlaskClient) -> None:
    client.get("/health")

    body = client.get("/metrics").get_data(as_text=True)

    assert 'loglens_http_requests_total{endpoint="health.health_check"' in body
