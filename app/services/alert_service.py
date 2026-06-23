from datetime import timedelta

from app.models import AlertRule
from app.repositories.alert_rule_repository import AlertRuleRepository
from app.repositories.log_entry_repository import LogEntryRepository
from app.schemas.log import (
    AlertEvaluation,
    AlertEvaluationParams,
    AlertRuleInput,
    LogLevel,
    TriggeredAlert,
)


class AlertService:
    def __init__(
        self,
        alert_repository: AlertRuleRepository,
        log_repository: LogEntryRepository,
    ) -> None:
        self._alert_repository = alert_repository
        self._log_repository = log_repository

    def create_rule(self, data: AlertRuleInput) -> AlertRule:
        rule = AlertRule(
            level=data.level.value,
            threshold=data.threshold,
            window_minutes=data.window_minutes,
        )
        return self._alert_repository.add(rule)

    def list_rules(self) -> list[AlertRule]:
        return self._alert_repository.list_all()

    def evaluate(self, params: AlertEvaluationParams) -> AlertEvaluation:
        reference = params.at or self._log_repository.latest_timestamp()
        if reference is None:
            return AlertEvaluation(reference_time=None, triggered=[])

        triggered: list[TriggeredAlert] = []
        for rule in self._alert_repository.list_all():
            window_start = reference - timedelta(minutes=rule.window_minutes)
            count = self._log_repository.count_in_window(
                level=rule.level,
                start=window_start,
                end=reference,
            )
            if count >= rule.threshold:
                triggered.append(
                    TriggeredAlert(
                        rule_id=rule.id,
                        level=LogLevel(rule.level),
                        threshold=rule.threshold,
                        window_minutes=rule.window_minutes,
                        count=count,
                        window_start=window_start,
                        window_end=reference,
                    )
                )

        return AlertEvaluation(reference_time=reference, triggered=triggered)


def build_alert_service() -> AlertService:
    return AlertService(AlertRuleRepository(), LogEntryRepository())
