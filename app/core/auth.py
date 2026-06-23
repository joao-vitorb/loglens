from flask import Flask, current_app, request

from app.config import Settings
from app.errors import UnauthorizedError

API_KEY_HEADER = "X-API-Key"
PROTECTED_PREFIX = "/api/"


def register_authentication(app: Flask) -> None:
    @app.before_request
    def enforce_api_key() -> None:
        if not request.path.startswith(PROTECTED_PREFIX):
            return

        settings: Settings = current_app.config["SETTINGS"]
        if not settings.api_key:
            return

        provided_key = request.headers.get(API_KEY_HEADER)
        if provided_key != settings.api_key:
            raise UnauthorizedError("Invalid or missing API key.")
