from datetime import UTC, datetime

from flask import Flask
from flask.testing import FlaskClient

from app.extensions import db
from app.models import LogEntry


def seed_errors(app: Flask) -> None:
    entries = [
        LogEntry(
            timestamp=datetime(2026, 6, 20, 8, 0, tzinfo=UTC),
            level="error",
            source="auth-service",
            message="login failed",
        ),
        LogEntry(
            timestamp=datetime(2026, 6, 20, 8, 1, tzinfo=UTC),
            level="error",
            source="auth-service",
            message="login failed",
        ),
        LogEntry(
            timestamp=datetime(2026, 6, 20, 8, 2, tzinfo=UTC),
            level="error",
            source="auth-service",
            message="login failed",
        ),
    ]
    db.session.add_all(entries)
    db.session.commit()


def test_create_alert_rule_returns_201(client: FlaskClient) -> None:
    response = client.post(
        "/api/v1/alerts",
        json={"level": "error", "threshold": 3, "window_minutes": 10},
    )
    body = response.get_json()

    assert response.status_code == 201
    assert body["id"] is not None
    assert body["level"] == "error"
    assert body["threshold"] == 3
    assert body["window_minutes"] == 10


def test_create_alert_rule_rejects_invalid_threshold(client: FlaskClient) -> None:
    response = client.post(
        "/api/v1/alerts",
        json={"level": "error", "threshold": 0, "window_minutes": 10},
    )

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_list_alert_rules_returns_created_rules(client: FlaskClient) -> None:
    client.post("/api/v1/alerts", json={"level": "error", "threshold": 3, "window_minutes": 10})
    client.post("/api/v1/alerts", json={"level": "warn", "threshold": 5, "window_minutes": 30})

    body = client.get("/api/v1/alerts").get_json()

    assert len(body) == 2
    assert {rule["level"] for rule in body} == {"error", "warn"}


def test_triggered_alerts_when_threshold_reached(client: FlaskClient, app: Flask) -> None:
    seed_errors(app)
    client.post("/api/v1/alerts", json={"level": "error", "threshold": 3, "window_minutes": 60})

    body = client.get("/api/v1/alerts/triggered").get_json()

    assert len(body["triggered"]) == 1
    alert = body["triggered"][0]
    assert alert["level"] == "error"
    assert alert["count"] == 3
    assert alert["threshold"] == 3


def test_not_triggered_when_threshold_not_reached(client: FlaskClient, app: Flask) -> None:
    seed_errors(app)
    client.post("/api/v1/alerts", json={"level": "error", "threshold": 10, "window_minutes": 60})

    body = client.get("/api/v1/alerts/triggered").get_json()

    assert body["triggered"] == []


def test_triggered_alerts_respects_window(client: FlaskClient, app: Flask) -> None:
    seed_errors(app)
    client.post("/api/v1/alerts", json={"level": "error", "threshold": 3, "window_minutes": 1})

    body = client.get("/api/v1/alerts/triggered?at=2026-06-20T08:02:00").get_json()

    assert body["triggered"] == []


def test_triggered_alerts_empty_without_logs(client: FlaskClient) -> None:
    client.post("/api/v1/alerts", json={"level": "error", "threshold": 1, "window_minutes": 60})

    body = client.get("/api/v1/alerts/triggered").get_json()

    assert body["reference_time"] is None
    assert body["triggered"] == []
