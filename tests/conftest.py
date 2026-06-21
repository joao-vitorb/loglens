import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app
from app.config import Settings


@pytest.fixture
def app() -> Flask:
    settings = Settings(environment="testing", debug=True, log_level="WARNING")
    application = create_app(settings)
    application.config.update(TESTING=True)
    return application


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()
