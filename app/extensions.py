from flasgger import Swagger
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from app.models.base import Base

db = SQLAlchemy(model_class=Base)

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
