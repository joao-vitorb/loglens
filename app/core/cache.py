import json
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

SUMMARY_KEY_PREFIX = "summary:"


class SummaryCache:
    def __init__(self, client: Redis | None, ttl_seconds: int) -> None:
        self._client = client
        self._ttl_seconds = ttl_seconds

    def get(self, key: str) -> dict[str, Any] | None:
        if self._client is None:
            return None
        try:
            raw = self._client.get(key)
        except RedisError:
            return None
        if raw is None:
            return None
        data: dict[str, Any] = json.loads(raw)
        return data

    def set(self, key: str, value: dict[str, Any]) -> None:
        if self._client is None:
            return
        try:
            self._client.set(key, json.dumps(value), ex=self._ttl_seconds)
        except RedisError:
            return

    def invalidate(self) -> None:
        if self._client is None:
            return
        try:
            for key in self._client.scan_iter(match=f"{SUMMARY_KEY_PREFIX}*"):
                self._client.delete(key)
        except RedisError:
            return


def build_summary_key(source: str | None, start: object, end: object, top_errors: int) -> str:
    return f"{SUMMARY_KEY_PREFIX}{source or ''}:{start or ''}:{end or ''}:{top_errors}"
