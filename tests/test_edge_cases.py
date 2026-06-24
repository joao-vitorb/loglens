from typing import Any

from flask import Flask
from redis.exceptions import RedisError

from app import create_app
from app.config import Settings, get_settings
from app.core.cache import SummaryCache
from app.extensions import build_redis_client, db
from app.models import LogEntry
from app.repositories.log_entry_repository import LogEntryRepository
from app.schemas.log import normalize_level_value
from app.services.log_parser import parse_log_content


def test_summary_cache_without_client_is_noop() -> None:
    cache = SummaryCache(None, ttl_seconds=60)

    cache.set("key", {"value": 1})

    assert cache.get("key") is None
    cache.invalidate()


class RaisingRedis:
    def get(self, key: str) -> str | None:
        raise RedisError("down")

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        raise RedisError("down")

    def scan_iter(self, match: str | None = None) -> list[str]:
        raise RedisError("down")


def test_summary_cache_swallows_redis_errors() -> None:
    cache = SummaryCache(RaisingRedis(), ttl_seconds=60)  # type: ignore[arg-type]

    assert cache.get("key") is None
    cache.set("key", {"value": 1})
    cache.invalidate()


def test_parse_log_content_handles_blank_and_malformed_lines() -> None:
    content = "\n2026-06-20T08:00:00 INFO svc started\nbroken\nnot-a-date ERROR svc boom\n"

    entries, errors = parse_log_content(content)

    assert len(entries) == 1
    reasons = sorted(error.reason for error in errors)
    assert reasons == ["invalid log entry", "malformed log line"]


def test_normalize_level_value_passes_through_non_string() -> None:
    assert normalize_level_value(123) == 123


def test_add_many_with_empty_list_is_noop(app: Flask) -> None:
    LogEntryRepository().add_many([])

    assert db.session.query(LogEntry).count() == 0


def test_build_redis_client_returns_none_without_url() -> None:
    assert build_redis_client(Settings(redis_url=None)) is None


def test_build_redis_client_returns_client_with_url() -> None:
    assert build_redis_client(Settings(redis_url="redis://localhost:6379/0")) is not None


def test_get_settings_returns_settings_instance() -> None:
    assert isinstance(get_settings(), Settings)


def test_unexpected_error_returns_internal_error() -> None:
    application = create_app(Settings(database_url="sqlite:///:memory:", rate_limit_enabled=False))

    @application.get("/boom")
    def boom() -> Any:
        raise RuntimeError("kaboom")

    application.config["PROPAGATE_EXCEPTIONS"] = False

    response = application.test_client().get("/boom")
    body = response.get_json()

    assert response.status_code == 500
    assert body["error"]["code"] == "INTERNAL_ERROR"
