from flask import current_app

from app.config import Settings
from app.schemas.log import AlertEvaluationParams, AlertNotification
from app.services.alert_service import AlertService, build_alert_service
from app.services.webhook_notifier import WebhookNotifier


class AlertNotificationService:
    def __init__(self, alert_service: AlertService, notifier: WebhookNotifier) -> None:
        self._alert_service = alert_service
        self._notifier = notifier

    def notify(self, params: AlertEvaluationParams) -> AlertNotification:
        evaluation = self._alert_service.evaluate(params)

        delivered = False
        if evaluation.triggered:
            delivered = self._notifier.notify(evaluation.model_dump(mode="json"))

        return AlertNotification(
            reference_time=evaluation.reference_time,
            triggered=evaluation.triggered,
            delivered=delivered,
        )


def build_alert_notification_service() -> AlertNotificationService:
    settings: Settings = current_app.config["SETTINGS"]
    notifier = WebhookNotifier(
        settings.alert_webhook_url,
        settings.alert_webhook_timeout_seconds,
    )
    return AlertNotificationService(build_alert_service(), notifier)
