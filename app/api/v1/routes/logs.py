from flask import Blueprint, Response, jsonify, request

from app.core.file_upload import read_log_file
from app.core.validation import validate_payload
from app.schemas.log import LogIngestionRequest
from app.services.ingestion_service import build_ingestion_service

logs_bp = Blueprint("logs", __name__)


@logs_bp.post("/logs")
def ingest_logs() -> tuple[Response, int]:
    """
    Ingest log entries from a JSON body.
    ---
    tags:
      - Logs
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            entries:
              type: array
              items:
                type: object
                properties:
                  timestamp:
                    type: string
                    format: date-time
                  level:
                    type: string
                    enum: [info, warn, error]
                  source:
                    type: string
                  message:
                    type: string
    responses:
      201:
        description: Ingestion result.
      422:
        description: Invalid request data.
    """
    data = validate_payload(LogIngestionRequest, request.get_json(silent=True))
    result = build_ingestion_service().ingest_entries(data.entries)
    return jsonify(result.model_dump()), 201


@logs_bp.post("/logs/upload")
def upload_logs() -> tuple[Response, int]:
    """
    Ingest log entries from a .log or .txt file upload.
    ---
    tags:
      - Logs
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: file
        type: file
        required: true
    responses:
      201:
        description: Ingestion result.
      400:
        description: Unsupported file type.
      413:
        description: File too large.
    """
    content = read_log_file(request.files.get("file"))
    result = build_ingestion_service().ingest_text(content)
    return jsonify(result.model_dump()), 201
