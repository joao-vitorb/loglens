from flask import Blueprint, Response, current_app, jsonify, request

from app.config import Settings
from app.core.cache import SummaryCache, build_summary_key
from app.core.file_upload import read_log_file
from app.core.validation import validate_payload
from app.extensions import limiter
from app.schemas.log import LogIngestionRequest, LogQueryParams, SummaryQueryParams
from app.services.ingestion_service import build_ingestion_service
from app.services.log_query_service import build_log_query_service
from app.services.summary_service import build_summary_service

logs_bp = Blueprint("logs", __name__)


def ingestion_rate_limit() -> str:
    settings: Settings = current_app.config["SETTINGS"]
    return settings.ingestion_rate_limit


def summary_cache() -> SummaryCache:
    cache: SummaryCache = current_app.config["SUMMARY_CACHE"]
    return cache


@logs_bp.post("/logs")
@limiter.limit(ingestion_rate_limit)
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
    summary_cache().invalidate()
    return jsonify(result.model_dump()), 201


@logs_bp.post("/logs/upload")
@limiter.limit(ingestion_rate_limit)
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
    summary_cache().invalidate()
    return jsonify(result.model_dump()), 201


@logs_bp.get("/logs")
def list_logs() -> tuple[Response, int]:
    """
    List log entries with optional filters and pagination.
    ---
    tags:
      - Logs
    parameters:
      - in: query
        name: level
        type: string
        enum: [info, warn, error]
      - in: query
        name: source
        type: string
      - in: query
        name: start
        type: string
        format: date-time
      - in: query
        name: end
        type: string
        format: date-time
      - in: query
        name: page
        type: integer
        default: 1
      - in: query
        name: page_size
        type: integer
        default: 20
    responses:
      200:
        description: A paginated list of log entries.
      422:
        description: Invalid query parameters.
    """
    params = validate_payload(LogQueryParams, request.args.to_dict())
    result = build_log_query_service().query(params)
    return jsonify(result.model_dump(mode="json")), 200


@logs_bp.get("/logs/summary")
def summarize_logs() -> tuple[Response, int]:
    """
    Summarize log entries: counts by level, top errors and time window.
    ---
    tags:
      - Logs
    parameters:
      - in: query
        name: source
        type: string
      - in: query
        name: start
        type: string
        format: date-time
      - in: query
        name: end
        type: string
        format: date-time
      - in: query
        name: top_errors
        type: integer
        default: 5
    responses:
      200:
        description: A summary of the matching log entries.
      422:
        description: Invalid query parameters.
    """
    params = validate_payload(SummaryQueryParams, request.args.to_dict())
    cache = summary_cache()
    cache_key = build_summary_key(params.source, params.start, params.end, params.top_errors)

    cached_summary = cache.get(cache_key)
    if cached_summary is not None:
        return jsonify(cached_summary), 200

    payload = build_summary_service().summarize(params).model_dump(mode="json")
    cache.set(cache_key, payload)
    return jsonify(payload), 200
