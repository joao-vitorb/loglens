from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LogLevel(StrEnum):
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


LEVEL_ALIASES = {"warning": "warn", "err": "error"}


def normalize_level_value(value: object) -> object:
    if isinstance(value, str):
        normalized = value.strip().lower()
        return LEVEL_ALIASES.get(normalized, normalized)
    return value


class LogEntryInput(BaseModel):
    timestamp: datetime
    level: LogLevel
    source: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1)

    @field_validator("level", mode="before")
    @classmethod
    def normalize_level(cls, value: object) -> object:
        return normalize_level_value(value)


class LogIngestionRequest(BaseModel):
    entries: list[LogEntryInput] = Field(min_length=1)


class LogEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    level: LogLevel
    source: str
    message: str
    created_at: datetime


class LineError(BaseModel):
    line: int
    reason: str


class IngestionResult(BaseModel):
    ingested: int
    skipped: int
    errors: list[LineError] = Field(default_factory=list)


class LogQueryParams(BaseModel):
    level: LogLevel | None = None
    source: str | None = Field(default=None, min_length=1, max_length=255)
    start: datetime | None = None
    end: datetime | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @field_validator("level", mode="before")
    @classmethod
    def normalize_level(cls, value: object) -> object:
        return normalize_level_value(value)


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class PaginatedLogs(BaseModel):
    items: list[LogEntryResponse]
    pagination: PaginationMeta
