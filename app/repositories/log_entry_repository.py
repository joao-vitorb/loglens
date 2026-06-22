from datetime import datetime

from sqlalchemy import ColumnElement, func, select

from app.extensions import db
from app.models import LogEntry


class LogEntryRepository:
    def add_many(self, entries: list[LogEntry]) -> None:
        if not entries:
            return
        db.session.add_all(entries)
        db.session.commit()

    def query(
        self,
        *,
        level: str | None,
        source: str | None,
        start: datetime | None,
        end: datetime | None,
        page: int,
        page_size: int,
    ) -> tuple[list[LogEntry], int]:
        conditions = self._build_conditions(level, source, start, end)

        count_statement = select(func.count()).select_from(LogEntry)
        items_statement = select(LogEntry)
        if conditions:
            count_statement = count_statement.where(*conditions)
            items_statement = items_statement.where(*conditions)

        total = db.session.scalar(count_statement) or 0
        items_statement = (
            items_statement.order_by(LogEntry.timestamp.desc(), LogEntry.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(db.session.scalars(items_statement))
        return items, total

    def _build_conditions(
        self,
        level: str | None,
        source: str | None,
        start: datetime | None,
        end: datetime | None,
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []
        if level is not None:
            conditions.append(LogEntry.level == level)
        if source is not None:
            conditions.append(LogEntry.source == source)
        if start is not None:
            conditions.append(LogEntry.timestamp >= start)
        if end is not None:
            conditions.append(LogEntry.timestamp <= end)
        return conditions
