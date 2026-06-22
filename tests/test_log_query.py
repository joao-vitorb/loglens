from datetime import UTC, datetime

from flask import Flask
from flask.testing import FlaskClient

from app.extensions import db
from app.models import LogEntry


def seed_entries(app: Flask) -> None:
    entries = [
        LogEntry(
            timestamp=datetime(2026, 6, 20, 8, 0, tzinfo=UTC),
            level="info",
            source="auth-service",
            message="started",
        ),
        LogEntry(
            timestamp=datetime(2026, 6, 20, 9, 0, tzinfo=UTC),
            level="error",
            source="auth-service",
            message="login failed",
        ),
        LogEntry(
            timestamp=datetime(2026, 6, 20, 10, 0, tzinfo=UTC),
            level="error",
            source="payment-service",
            message="gateway timeout",
        ),
    ]
    db.session.add_all(entries)
    db.session.commit()


def test_list_logs_returns_all_with_pagination_meta(client: FlaskClient, app: Flask) -> None:
    seed_entries(app)

    response = client.get("/api/v1/logs")
    body = response.get_json()

    assert response.status_code == 200
    assert body["pagination"] == {"page": 1, "page_size": 20, "total": 3, "total_pages": 1}
    assert len(body["items"]) == 3


def test_list_logs_orders_by_timestamp_desc(client: FlaskClient, app: Flask) -> None:
    seed_entries(app)

    body = client.get("/api/v1/logs").get_json()

    timestamps = [item["timestamp"] for item in body["items"]]
    assert timestamps == sorted(timestamps, reverse=True)


def test_list_logs_filters_by_level(client: FlaskClient, app: Flask) -> None:
    seed_entries(app)

    body = client.get("/api/v1/logs?level=ERROR").get_json()

    assert body["pagination"]["total"] == 2
    assert all(item["level"] == "error" for item in body["items"])


def test_list_logs_filters_by_source(client: FlaskClient, app: Flask) -> None:
    seed_entries(app)

    body = client.get("/api/v1/logs?source=payment-service").get_json()

    assert body["pagination"]["total"] == 1
    assert body["items"][0]["source"] == "payment-service"


def test_list_logs_filters_by_time_range(client: FlaskClient, app: Flask) -> None:
    seed_entries(app)

    body = client.get("/api/v1/logs?start=2026-06-20T08:30:00&end=2026-06-20T09:30:00").get_json()

    assert body["pagination"]["total"] == 1
    assert body["items"][0]["message"] == "login failed"


def test_list_logs_paginates_results(client: FlaskClient, app: Flask) -> None:
    seed_entries(app)

    body = client.get("/api/v1/logs?page=1&page_size=2").get_json()

    assert body["pagination"] == {"page": 1, "page_size": 2, "total": 3, "total_pages": 2}
    assert len(body["items"]) == 2


def test_list_logs_rejects_invalid_page_size(client: FlaskClient) -> None:
    response = client.get("/api/v1/logs?page_size=500")
    body = response.get_json()

    assert response.status_code == 422
    assert body["error"]["code"] == "VALIDATION_ERROR"
