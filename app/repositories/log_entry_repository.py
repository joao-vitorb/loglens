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

    def count_by_level(
        self,
        *,
        source: str | None,
        start: datetime | None,
        end: datetime | None,
    ) -> dict[str, int]:
        conditions = self._build_conditions(None, source, start, end)
        statement = select(LogEntry.level, func.count()).group_by(LogEntry.level)
        if conditions:
            statement = statement.where(*conditions)
        rows = db.session.execute(statement).all()
        return {level: count for level, count in rows}

    def top_error_messages(
        self,
        *,
        source: str | None,
        start: datetime | None,
        end: datetime | None,
        limit: int,
    ) -> list[tuple[str, int]]:
        conditions = self._build_conditions("error", source, start, end)
        statement = (
            select(LogEntry.message, func.count().label("occurrences"))
            .where(*conditions)
            .group_by(LogEntry.message)
            .order_by(func.count().desc(), LogEntry.message)
            .limit(limit)
        )
        rows = db.session.execute(statement).all()
        return [(message, count) for message, count in rows]

    def time_window(
        self,
        *,
        source: str | None,
        start: datetime | None,
        end: datetime | None,
    ) -> tuple[datetime | None, datetime | None]:
        conditions = self._build_conditions(None, source, start, end)
        statement = select(func.min(LogEntry.timestamp), func.max(LogEntry.timestamp))
        if conditions:
            statement = statement.where(*conditions)
        earliest, latest = db.session.execute(statement).one()
        return earliest, latest

    def latest_timestamp(self) -> datetime | None:
        return db.session.scalar(select(func.max(LogEntry.timestamp)))

    def count_in_window(self, *, level: str, start: datetime, end: datetime) -> int:
        statement = (
            select(func.count())
            .select_from(LogEntry)
            .where(
                LogEntry.level == level,
                LogEntry.timestamp >= start,
                LogEntry.timestamp <= end,
            )
        )
        return db.session.scalar(statement) or 0

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
