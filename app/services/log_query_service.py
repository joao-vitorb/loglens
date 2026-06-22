from math import ceil

from app.repositories.log_entry_repository import LogEntryRepository
from app.schemas.log import (
    LogEntryResponse,
    LogQueryParams,
    PaginatedLogs,
    PaginationMeta,
)


class LogQueryService:
    def __init__(self, repository: LogEntryRepository) -> None:
        self._repository = repository

    def query(self, params: LogQueryParams) -> PaginatedLogs:
        items, total = self._repository.query(
            level=params.level.value if params.level else None,
            source=params.source,
            start=params.start,
            end=params.end,
            page=params.page,
            page_size=params.page_size,
        )
        return PaginatedLogs(
            items=[LogEntryResponse.model_validate(item) for item in items],
            pagination=PaginationMeta(
                page=params.page,
                page_size=params.page_size,
                total=total,
                total_pages=ceil(total / params.page_size) if total else 0,
            ),
        )


def build_log_query_service() -> LogQueryService:
    return LogQueryService(LogEntryRepository())
