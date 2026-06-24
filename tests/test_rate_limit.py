from collections.abc import Iterator

import pytest
from flask import Flask

from app import create_app
from app.config import Settings
from app.extensions import db, limiter


@pytest.fixture
def limited_app() -> Iterator[Flask]:
    settings = Settings(
        environment="testing",
        database_url="sqlite:///:memory:",
        ingestion_rate_limit="2/minute",
        rate_limit_enabled=True,
    )
    application = create_app(settings)
    limiter.reset()
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


def ingest(application: Flask) -> int:
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
    return application.test_client().post("/api/v1/logs", json=payload).status_code


def test_ingestion_is_rate_limited(limited_app: Flask) -> None:
    assert ingest(limited_app) == 201
    assert ingest(limited_app) == 201

    response = limited_app.test_client().post(
        "/api/v1/logs",
        json={
            "entries": [
                {
                    "timestamp": "2026-06-20T08:00:00",
                    "level": "info",
                    "source": "svc",
                    "message": "ok",
                }
            ]
        },
    )

    assert response.status_code == 429
