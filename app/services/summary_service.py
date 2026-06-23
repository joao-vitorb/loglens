from app.repositories.log_entry_repository import LogEntryRepository
from app.schemas.log import (
    LevelCounts,
    LogSummary,
    SummaryQueryParams,
    TimeWindow,
    TopError,
)


class SummaryService:
    def __init__(self, repository: LogEntryRepository) -> None:
        self._repository = repository

    def summarize(self, params: SummaryQueryParams) -> LogSummary:
        counts = self._repository.count_by_level(
            source=params.source,
            start=params.start,
            end=params.end,
        )
        top_errors = self._repository.top_error_messages(
            source=params.source,
            start=params.start,
            end=params.end,
            limit=params.top_errors,
        )
        earliest, latest = self._repository.time_window(
            source=params.source,
            start=params.start,
            end=params.end,
        )

        return LogSummary(
            total=sum(counts.values()),
            counts_by_level=LevelCounts(
                info=counts.get("info", 0),
                warn=counts.get("warn", 0),
                error=counts.get("error", 0),
            ),
            top_errors=[TopError(message=message, count=count) for message, count in top_errors],
            time_window=TimeWindow(start=earliest, end=latest),
        )


def build_summary_service() -> SummaryService:
    return SummaryService(LogEntryRepository())
