from flask import Blueprint, Response, jsonify, request

from app.core.validation import validate_payload
from app.observability.metrics import ALERTS_TRIGGERED
from app.schemas.log import AlertEvaluationParams, AlertRuleInput, AlertRuleResponse
from app.services.alert_notification_service import build_alert_notification_service
from app.services.alert_service import build_alert_service

alerts_bp = Blueprint("alerts", __name__)


@alerts_bp.post("/alerts")
def create_alert_rule() -> tuple[Response, int]:
    """
    Create an alert rule.
    ---
    tags:
      - Alerts
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            level:
              type: string
              enum: [info, warn, error]
            threshold:
              type: integer
            window_minutes:
              type: integer
    responses:
      201:
        description: The created alert rule.
      422:
        description: Invalid request data.
    """
    data = validate_payload(AlertRuleInput, request.get_json(silent=True))
    rule = build_alert_service().create_rule(data)
    return jsonify(AlertRuleResponse.model_validate(rule).model_dump(mode="json")), 201


@alerts_bp.get("/alerts")
def list_alert_rules() -> tuple[Response, int]:
    """
    List alert rules.
    ---
    tags:
      - Alerts
    responses:
      200:
        description: A list of alert rules.
    """
    rules = build_alert_service().list_rules()
    payload = [AlertRuleResponse.model_validate(rule).model_dump(mode="json") for rule in rules]
    return jsonify(payload), 200


@alerts_bp.get("/alerts/triggered")
def list_triggered_alerts() -> tuple[Response, int]:
    """
    Evaluate alert rules and return the ones currently triggered.
    ---
    tags:
      - Alerts
    parameters:
      - in: query
        name: at
        type: string
        format: date-time
        description: Reference time for evaluation (defaults to the latest log timestamp).
    responses:
      200:
        description: The triggered alerts at the reference time.
      422:
        description: Invalid query parameters.
    """
    params = validate_payload(AlertEvaluationParams, request.args.to_dict())
    evaluation = build_alert_service().evaluate(params)
    ALERTS_TRIGGERED.inc(len(evaluation.triggered))
    return jsonify(evaluation.model_dump(mode="json")), 200


@alerts_bp.post("/alerts/notify")
def notify_triggered_alerts() -> tuple[Response, int]:
    """
    Evaluate alert rules and deliver triggered alerts to the configured webhook.
    ---
    tags:
      - Alerts
    parameters:
      - in: query
        name: at
        type: string
        format: date-time
        description: Reference time for evaluation (defaults to the latest log timestamp).
    responses:
      200:
        description: The triggered alerts and whether they were delivered.
      422:
        description: Invalid query parameters.
      502:
        description: The webhook delivery failed.
    """
    params = validate_payload(AlertEvaluationParams, request.args.to_dict())
    result = build_alert_notification_service().notify(params)
    return jsonify(result.model_dump(mode="json")), 200
