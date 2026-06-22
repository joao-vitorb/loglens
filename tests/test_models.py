from datetime import UTC, datetime

from flask import Flask

from app.extensions import db
from app.models import AlertRule, LogEntry


def test_log_entry_is_persisted(app: Flask) -> None:
    entry = LogEntry(
        timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        level="error",
        source="auth-service",
        message="login failed",
    )
    db.session.add(entry)
    db.session.commit()

    stored = db.session.get(LogEntry, entry.id)

    assert stored is not None
    assert stored.level == "error"
    assert stored.created_at is not None


def test_alert_rule_is_persisted(app: Flask) -> None:
    rule = AlertRule(level="error", threshold=5, window_minutes=10)
    db.session.add(rule)
    db.session.commit()

    stored = db.session.get(AlertRule, rule.id)

    assert stored is not None
    assert stored.threshold == 5
    assert stored.window_minutes == 10
