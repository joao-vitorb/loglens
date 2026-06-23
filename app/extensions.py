from flasgger import Swagger
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from redis import Redis

from app.config import Settings
from app.models.base import Base

db = SQLAlchemy(model_class=Base)
limiter = Limiter(key_func=get_remote_address)


def build_redis_client(settings: Settings) -> Redis | None:
    if not settings.redis_url:
        return None
    return Redis.from_url(settings.redis_url, decode_responses=True)


def init_limiter(app: Flask, settings: Settings) -> None:
    app.config["RATELIMIT_STORAGE_URI"] = settings.redis_url or "memory://"
    app.config["RATELIMIT_ENABLED"] = settings.rate_limit_enabled
    limiter.init_app(app)


swagger_template = {
    "info": {
        "title": "LogLens API",
        "description": "REST microservice for log analysis.",
        "version": "1.0.0",
    }
}

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/",
}


def init_swagger(app: Flask) -> Swagger:
    return Swagger(app, template=swagger_template, config=swagger_config)
