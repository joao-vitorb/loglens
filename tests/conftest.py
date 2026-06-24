from collections.abc import Iterator

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app
from app.config import Settings
from app.extensions import db


@pytest.fixture
def app() -> Iterator[Flask]:
    settings = Settings(
        environment="testing",
        debug=True,
        log_level="WARNING",
        database_url="sqlite:///:memory:",
        rate_limit_enabled=False,
    )
    application = create_app(settings)
    application.config.update(TESTING=True)

    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()
