import io

from flask import Flask
from flask.testing import FlaskClient

from app.extensions import db
from app.models import LogEntry


def count_entries(app: Flask) -> int:
    return db.session.query(LogEntry).count()


def test_ingest_json_entries_persists_logs(client: FlaskClient, app: Flask) -> None:
    payload = {
        "entries": [
            {
                "timestamp": "2026-06-20T08:00:00",
                "level": "ERROR",
                "source": "auth-service",
                "message": "login failed",
            },
            {
                "timestamp": "2026-06-20T08:01:00",
                "level": "info",
                "source": "auth-service",
                "message": "user logged in",
            },
        ]
    }

    response = client.post("/api/v1/logs", json=payload)
    body = response.get_json()

    assert response.status_code == 201
    assert body == {"ingested": 2, "skipped": 0, "errors": []}
    assert count_entries(app) == 2


def test_ingest_json_normalizes_level(client: FlaskClient, app: Flask) -> None:
    payload = {
        "entries": [
            {
                "timestamp": "2026-06-20T08:00:00",
                "level": "WARNING",
                "source": "payment-service",
                "message": "high latency",
            }
        ]
    }

    response = client.post("/api/v1/logs", json=payload)

    assert response.status_code == 201
    stored = db.session.query(LogEntry).one()
    assert stored.level == "warn"


def test_ingest_json_invalid_entry_returns_422(client: FlaskClient) -> None:
    payload = {"entries": [{"level": "error", "source": "auth", "message": "no timestamp"}]}

    response = client.post("/api/v1/logs", json=payload)
    body = response.get_json()

    assert response.status_code == 422
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_upload_valid_file_ingests_and_skips_malformed(client: FlaskClient, app: Flask) -> None:
    content = (
        "2026-06-20T08:00:00 INFO auth-service started\n"
        "this line is malformed\n"
        "2026-06-20T08:01:00 ERROR auth-service login failed\n"
    )
    data = {"file": (io.BytesIO(content.encode("utf-8")), "app.log")}

    response = client.post("/api/v1/logs/upload", data=data, content_type="multipart/form-data")
    body = response.get_json()

    assert response.status_code == 201
    assert body["ingested"] == 2
    assert body["skipped"] == 1
    assert count_entries(app) == 2


def test_upload_unsupported_extension_returns_400(client: FlaskClient) -> None:
    data = {"file": (io.BytesIO(b"2026-06-20T08:00:00 INFO svc ok"), "logs.csv")}

    response = client.post("/api/v1/logs/upload", data=data, content_type="multipart/form-data")
    body = response.get_json()

    assert response.status_code == 400
    assert body["error"]["code"] == "UNSUPPORTED_FILE_TYPE"


def test_upload_without_file_returns_422(client: FlaskClient) -> None:
    response = client.post("/api/v1/logs/upload", data={}, content_type="multipart/form-data")
    body = response.get_json()

    assert response.status_code == 422
    assert body["error"]["code"] == "VALIDATION_ERROR"
