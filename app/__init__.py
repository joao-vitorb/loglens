from flask import Flask

from app import models
from app.api.health import health_bp
from app.api.v1 import api_v1
from app.config import Settings, get_settings
from app.core.auth import register_authentication
from app.core.cache import SummaryCache
from app.errors import register_error_handlers
from app.extensions import build_redis_client, db, init_limiter, init_swagger
from app.logging_config import configure_logging


def create_app(settings: Settings | None = None) -> Flask:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = Flask(__name__)
    app.config["SETTINGS"] = settings
    app.config["DEBUG"] = settings.debug
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.database_url
    app.config["MAX_CONTENT_LENGTH"] = settings.max_upload_bytes

    redis_client = build_redis_client(settings)
    app.config["SUMMARY_CACHE"] = SummaryCache(redis_client, settings.summary_cache_ttl_seconds)

    db.init_app(app)
    init_limiter(app, settings)
    init_swagger(app)
    register_error_handlers(app)
    register_authentication(app)
    app.register_blueprint(health_bp)
    app.register_blueprint(api_v1)

    return app


__all__ = ["create_app", "models"]
