from app.extensions import db
from app.models import LogEntry


class LogEntryRepository:
    def add_many(self, entries: list[LogEntry]) -> None:
        if not entries:
            return
        db.session.add_all(entries)
        db.session.commit()
