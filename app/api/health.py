from flask import Blueprint, Response, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check() -> Response:
    """
    Health check endpoint.
    ---
    tags:
      - Health
    responses:
      200:
        description: Service is healthy.
    """
    return jsonify({"status": "ok"})
