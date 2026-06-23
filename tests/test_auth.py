from collections.abc import Iterator

import pytest
from flask import Flask

from app import create_app
from app.config import Settings
from app.extensions import db


@pytest.fixture
def secured_app() -> Iterator[Flask]:
    settings = Settings(
        environment="testing",
        database_url="sqlite:///:memory:",
        rate_limit_enabled=False,
        api_key="secret-key",
    )
    application = create_app(settings)
    with application.app_context():
        db.create_all()
        yield application
        db.drop_all()


def test_request_without_api_key_is_rejected(secured_app: Flask) -> None:
    response = secured_app.test_client().get("/api/v1/logs")
    body = response.get_json()

    assert response.status_code == 401
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_request_with_wrong_api_key_is_rejected(secured_app: Flask) -> None:
    response = secured_app.test_client().get("/api/v1/logs", headers={"X-API-Key": "wrong"})

    assert response.status_code == 401


def test_request_with_correct_api_key_is_allowed(secured_app: Flask) -> None:
    response = secured_app.test_client().get("/api/v1/logs", headers={"X-API-Key": "secret-key"})

    assert response.status_code == 200


def test_health_is_public(secured_app: Flask) -> None:
    response = secured_app.test_client().get("/health")

    assert response.status_code == 200
