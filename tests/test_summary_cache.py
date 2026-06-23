from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import pytest
from flask import Flask

from app import create_app
from app.config import Settings
from app.core.cache import SummaryCache
from app.extensions import db
from app.models import LogEntry


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.store[key] = value

    def scan_iter(self, match: str | None = None) -> list[str]:
        prefix = match.rstrip("*") if match else ""
        return [key for key in list(self.store) if key.startswith(prefix)]

    def delete(self, key: str) -> None:
        self.store.pop(key, None)


@pytest.fixture
def cached_app() -> Iterator[Flask]:
    settings = Settings(
        environment="testing",
        database_url="sqlite:///:memory:",
        rate_limit_enabled=False,
    )
    application = create_app(settings)
    with application.app_context():
        db.create_all()
        application.config["SUMMARY_CACHE"] = SummaryCache(FakeRedis(), ttl_seconds=60)  # type: ignore[arg-type]
        yield application
        db.drop_all()


def add_error(timestamp: datetime) -> None:
    db.session.add(LogEntry(timestamp=timestamp, level="error", source="svc", message="boom"))
    db.session.commit()


def summary_total(application: Flask) -> Any:
    return application.test_client().get("/api/v1/logs/summary").get_json()["total"]


def test_summary_is_served_from_cache(cached_app: Flask) -> None:
    add_error(datetime(2026, 6, 20, 8, 0, tzinfo=UTC))

    assert summary_total(cached_app) == 1

    add_error(datetime(2026, 6, 20, 8, 1, tzinfo=UTC))

    assert summary_total(cached_app) == 1


def test_ingestion_invalidates_summary_cache(cached_app: Flask) -> None:
    add_error(datetime(2026, 6, 20, 8, 0, tzinfo=UTC))
    assert summary_total(cached_app) == 1

    cached_app.test_client().post(
        "/api/v1/logs",
        json={
            "entries": [
                {
                    "timestamp": "2026-06-20T09:00:00",
                    "level": "error",
                    "source": "svc",
                    "message": "boom",
                }
            ]
        },
    )

    assert summary_total(cached_app) == 2
