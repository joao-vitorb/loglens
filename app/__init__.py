from flask import Flask

from app import models
from app.api.health import health_bp
from app.api.v1 import api_v1
from app.config import Settings, get_settings
from app.errors import register_error_handlers
from app.extensions import db, init_swagger
from app.logging_config import configure_logging


def create_app(settings: Settings | None = None) -> Flask:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = Flask(__name__)
    app.config["SETTINGS"] = settings
    app.config["DEBUG"] = settings.debug
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.database_url

    db.init_app(app)
    init_swagger(app)
    register_error_handlers(app)
    app.register_blueprint(health_bp)
    app.register_blueprint(api_v1)

    return app


__all__ = ["create_app", "models"]
