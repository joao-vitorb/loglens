from app.models import LogEntry
from app.repositories.log_entry_repository import LogEntryRepository
from app.schemas.log import IngestionResult, LogEntryInput
from app.services.log_parser import parse_log_content


class IngestionService:
    def __init__(self, repository: LogEntryRepository) -> None:
        self._repository = repository

    def ingest_entries(self, entries: list[LogEntryInput]) -> IngestionResult:
        models = [self._to_model(entry) for entry in entries]
        self._repository.add_many(models)
        return IngestionResult(ingested=len(models), skipped=0)

    def ingest_text(self, content: str) -> IngestionResult:
        entries, errors = parse_log_content(content)
        models = [self._to_model(entry) for entry in entries]
        self._repository.add_many(models)
        return IngestionResult(ingested=len(models), skipped=len(errors), errors=errors)

    def _to_model(self, entry: LogEntryInput) -> LogEntry:
        return LogEntry(
            timestamp=entry.timestamp,
            level=entry.level.value,
            source=entry.source,
            message=entry.message,
        )


def build_ingestion_service() -> IngestionService:
    return IngestionService(LogEntryRepository())
