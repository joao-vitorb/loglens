from flasgger import Swagger
from flask import Flask

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
    "specs_route": "/docs",
}


def init_swagger(app: Flask) -> Swagger:
    return Swagger(app, template=swagger_template, config=swagger_config)
