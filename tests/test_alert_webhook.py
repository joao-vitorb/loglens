from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any

import pytest
import requests
from flask import Flask

from app import create_app
from app.config import Settings
from app.extensions import db
from app.models import AlertRule, LogEntry


class FakeResponse:
    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")


@contextmanager
def running_app(webhook_url: str | None) -> Iterator[Flask]:
    settings = Settings(
        environment="testing",
        database_url="sqlite:///:memory:",
        alert_webhook_url=webhook_url,
    )
    application = create_app(settings)
    application.config.update(TESTING=True)
    with application.app_context():
        db.create_all()
        try:
            yield application
        finally:
            db.session.remove()
            db.drop_all()
            db.engine.dispose()


def seed_rule_and_errors(application: Flask) -> None:
    db.session.add_all(
        [
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
            AlertRule(level="error", threshold=2, window_minutes=60),
        ]
    )
    db.session.commit()


@pytest.fixture
def captured_posts(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def fake_post(url: str, json: dict[str, Any], timeout: float) -> FakeResponse:
        calls.append({"url": url, "json": json, "timeout": timeout})
        return FakeResponse(200)

    monkeypatch.setattr("app.services.webhook_notifier.requests.post", fake_post)
    return calls


def test_notify_delivers_to_webhook_when_triggered(
    captured_posts: list[dict[str, Any]],
) -> None:
    with running_app("http://hook.test/alerts") as application:
        seed_rule_and_errors(application)
        body = application.test_client().post("/api/v1/alerts/notify").get_json()

    assert body["delivered"] is True
    assert len(body["triggered"]) == 1
    assert len(captured_posts) == 1
    assert captured_posts[0]["url"] == "http://hook.test/alerts"
    assert captured_posts[0]["json"]["triggered"][0]["count"] == 2


def test_notify_does_not_deliver_without_webhook_configured(
    captured_posts: list[dict[str, Any]],
) -> None:
    with running_app(None) as application:
        seed_rule_and_errors(application)
        body = application.test_client().post("/api/v1/alerts/notify").get_json()

    assert body["delivered"] is False
    assert len(body["triggered"]) == 1
    assert captured_posts == []


def test_notify_does_not_deliver_when_nothing_triggered(
    captured_posts: list[dict[str, Any]],
) -> None:
    with running_app("http://hook.test/alerts") as application:
        body = application.test_client().post("/api/v1/alerts/notify").get_json()

    assert body["delivered"] is False
    assert body["triggered"] == []
    assert captured_posts == []


@pytest.fixture
def failing_post(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    def fake_post(url: str, json: dict[str, Any], timeout: float) -> FakeResponse:
        raise requests.ConnectionError("unreachable")

    monkeypatch.setattr("app.services.webhook_notifier.requests.post", fake_post)
    yield


def test_notify_returns_502_when_webhook_fails(failing_post: None) -> None:
    with running_app("http://hook.test/alerts") as application:
        seed_rule_and_errors(application)
        response = application.test_client().post("/api/v1/alerts/notify")
        body = response.get_json()

    assert response.status_code == 502
    assert body["error"]["code"] == "WEBHOOK_DELIVERY_FAILED"
