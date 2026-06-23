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
            level="warn",
            source="auth-service",
            message="slow response",
        ),
        LogEntry(
            timestamp=datetime(2026, 6, 20, 10, 0, tzinfo=UTC),
            level="error",
            source="auth-service",
            message="login failed",
        ),
        LogEntry(
            timestamp=datetime(2026, 6, 20, 11, 0, tzinfo=UTC),
            level="error",
            source="payment-service",
            message="gateway timeout",
        ),
        LogEntry(
            timestamp=datetime(2026, 6, 20, 12, 0, tzinfo=UTC),
            level="error",
            source="payment-service",
            message="gateway timeout",
        ),
    ]
    db.session.add_all(entries)
    db.session.commit()


def test_summary_returns_counts_by_level_and_total(client: FlaskClient, app: Flask) -> None:
    seed_entries(app)

    body = client.get("/api/v1/logs/summary").get_json()

    assert body["total"] == 5
    assert body["counts_by_level"] == {"info": 1, "warn": 1, "error": 3}


def test_summary_returns_top_errors_ordered_by_count(client: FlaskClient, app: Flask) -> None:
    seed_entries(app)

    body = client.get("/api/v1/logs/summary").get_json()

    assert body["top_errors"][0] == {"message": "gateway timeout", "count": 2}
    assert {"message": "login failed", "count": 1} in body["top_errors"]


def test_summary_returns_time_window(client: FlaskClient, app: Flask) -> None:
    seed_entries(app)

    body = client.get("/api/v1/logs/summary").get_json()

    assert body["time_window"]["start"].startswith("2026-06-20T08:00:00")
    assert body["time_window"]["end"].startswith("2026-06-20T12:00:00")


def test_summary_filters_by_source(client: FlaskClient, app: Flask) -> None:
    seed_entries(app)

    body = client.get("/api/v1/logs/summary?source=payment-service").get_json()

    assert body["total"] == 2
    assert body["counts_by_level"] == {"info": 0, "warn": 0, "error": 2}
    assert body["top_errors"] == [{"message": "gateway timeout", "count": 2}]


def test_summary_respects_top_errors_limit(client: FlaskClient, app: Flask) -> None:
    seed_entries(app)

    body = client.get("/api/v1/logs/summary?top_errors=1").get_json()

    assert len(body["top_errors"]) == 1


def test_summary_on_empty_database(client: FlaskClient) -> None:
    body = client.get("/api/v1/logs/summary").get_json()

    assert body["total"] == 0
    assert body["counts_by_level"] == {"info": 0, "warn": 0, "error": 0}
    assert body["top_errors"] == []
    assert body["time_window"] == {"start": None, "end": None}
