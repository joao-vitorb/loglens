from sqlalchemy import select

from app.extensions import db
from app.models import AlertRule


class AlertRuleRepository:
    def add(self, rule: AlertRule) -> AlertRule:
        db.session.add(rule)
        db.session.commit()
        db.session.refresh(rule)
        return rule

    def list_all(self) -> list[AlertRule]:
        return list(db.session.scalars(select(AlertRule).order_by(AlertRule.id)))
