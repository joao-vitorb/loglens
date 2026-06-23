from typing import Any

import requests

from app.errors import WebhookError


class WebhookNotifier:
    def __init__(self, url: str | None, timeout_seconds: float) -> None:
        self._url = url
        self._timeout_seconds = timeout_seconds

    def is_enabled(self) -> bool:
        return bool(self._url)

    def notify(self, payload: dict[str, Any]) -> bool:
        if not self._url:
            return False
        try:
            response = requests.post(self._url, json=payload, timeout=self._timeout_seconds)
            response.raise_for_status()
        except requests.RequestException as error:
            raise WebhookError("Failed to deliver alert webhook.") from error
        return True
