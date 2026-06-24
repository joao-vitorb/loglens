# LogLens

REST microservice for log analysis. It ingests logs (JSON or file upload),
parses the entries and returns summaries and alerts: counts by level, top
errors, occurrences per time window and threshold-based alerts.

## Table of contents

- [Features](#features)
- [Tech stack](#tech-stack)
- [Architecture](#architecture)
- [Setup](#setup)
- [Configuration](#configuration)
- [Database](#database)
- [Running](#running)
- [Authentication](#authentication)
- [Caching and rate limiting](#caching-and-rate-limiting)
- [Metrics](#metrics)
- [Error format](#error-format)
- [API endpoints](#api-endpoints)
- [Seed example data](#seed-example-data)
- [Development](#development)
- [Project structure](#project-structure)

## Features

- Log ingestion via JSON and via `.log` / `.txt` file upload
- Line parsing with reporting of malformed and invalid entries
- Listing with filters (level, source, time range) and pagination
- Summaries: counts by level, top error messages and time window
- Threshold-based alert rules with evaluation and webhook delivery
- API key authentication, Redis summary cache and ingestion rate limiting
- Prometheus metrics and Swagger documentation

## Tech stack

- Python 3.12
- Flask (blueprints)
- SQLAlchemy + Flask-SQLAlchemy
- Alembic (database migrations)
- PostgreSQL (SQLite for local development and tests)
- Pydantic / pydantic-settings
- Redis (cache) and Flask-Limiter (rate limiting)
- structlog (structured logging)
- prometheus-client (metrics)
- flasgger (Swagger UI)
- Ruff, mypy, pre-commit
- PyTest

## Architecture

The code is organized in clear layers, each with a single responsibility:

- **Routes** (`app/api`): HTTP handling and request/response shaping.
- **Schemas** (`app/schemas`): Pydantic models for input and output validation.
- **Services** (`app/services`): business logic (parsing, ingestion, summaries, alerts).
- **Repositories** (`app/repositories`): database access with SQLAlchemy.
- **Models** (`app/models`): SQLAlchemy ORM entities.
- **Core** (`app/core`): cross-cutting concerns (auth, validation, caching, uploads).

## Setup

Requires Python 3.12 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

On Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Configuration

Settings are read from environment variables (prefix `LOGLENS_`). All values have
safe defaults for local development.

| Variable | Default | Description |
|----------|---------|-------------|
| `LOGLENS_APP_NAME` | `LogLens` | Application name |
| `LOGLENS_ENVIRONMENT` | `development` | Runtime environment |
| `LOGLENS_DEBUG` | `false` | Enable debug mode |
| `LOGLENS_LOG_LEVEL` | `INFO` | Logging level |
| `LOGLENS_DATABASE_URL` | `sqlite:///loglens.db` | SQLAlchemy database URL |
| `LOGLENS_MAX_UPLOAD_BYTES` | `5242880` | Maximum upload size in bytes |
| `LOGLENS_ALERT_WEBHOOK_URL` | _(none)_ | Webhook URL to deliver triggered alerts |
| `LOGLENS_ALERT_WEBHOOK_TIMEOUT_SECONDS` | `5.0` | Webhook request timeout |
| `LOGLENS_API_KEY` | _(none)_ | When set, `/api/*` requires the `X-API-Key` header |
| `LOGLENS_REDIS_URL` | _(none)_ | Redis URL for summary cache and rate limit storage |
| `LOGLENS_SUMMARY_CACHE_TTL_SECONDS` | `60` | Summary cache TTL |
| `LOGLENS_INGESTION_RATE_LIMIT` | `60/minute` | Rate limit for ingestion endpoints |
| `LOGLENS_RATE_LIMIT_ENABLED` | `true` | Enable or disable rate limiting |

For PostgreSQL via Docker:

```
LOGLENS_DATABASE_URL=postgresql+psycopg://loglens:loglens@localhost:5432/loglens
```

## Database

Start PostgreSQL and Redis with Docker:

```bash
docker compose up -d
```

Apply migrations:

```bash
alembic upgrade head
```

Create a new migration after changing models:

```bash
alembic revision --autogenerate -m "describe change"
```

## Running

```bash
flask --app wsgi run --debug
```

The API will be available at `http://localhost:5000`.

- Health check: `GET /health`
- API docs (Swagger UI): `GET /docs`
- Metrics (Prometheus): `GET /metrics`

## Authentication

When `LOGLENS_API_KEY` is set, every `/api/*` request must include the API key
in the `X-API-Key` header. `/health`, `/docs` and `/metrics` stay public. If the
variable is not set, authentication is disabled (useful for local development).

In the Swagger UI, use the **Authorize** button to set the API key.

## Caching and rate limiting

When `LOGLENS_REDIS_URL` is set, summary responses are cached in Redis (TTL from
`LOGLENS_SUMMARY_CACHE_TTL_SECONDS`) and invalidated whenever new logs are
ingested. Ingestion endpoints are rate limited (`LOGLENS_INGESTION_RATE_LIMIT`);
without Redis the limiter falls back to in-memory storage.

## Metrics

`GET /metrics` exposes Prometheus-formatted metrics (public, like `/health`):
HTTP request counts and latency per endpoint, total ingested log entries and
total triggered alerts.

## Error format

Errors share a consistent JSON structure with an internal `code`:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data.",
    "details": [{ "field": "page_size", "message": "Input should be less than or equal to 100" }]
  }
}
```

Common status codes: `400` (unsupported file type), `401` (missing/invalid API
key), `413` (upload too large), `422` (validation), `429` (rate limit) and `502`
(webhook delivery failed).

## API endpoints

### Ingest logs (JSON)

```
POST /api/v1/logs
Content-Type: application/json

{
  "entries": [
    {
      "timestamp": "2026-06-20T08:00:00",
      "level": "error",
      "source": "auth-service",
      "message": "login failed"
    }
  ]
}
```

### Ingest logs (file upload)

```
POST /api/v1/logs/upload
Content-Type: multipart/form-data
field: file = <a .log or .txt file>
```

Each line must follow the format `TIMESTAMP LEVEL SOURCE MESSAGE`, for example:

```
2026-06-20T08:00:00 ERROR auth-service login failed
```

Malformed or invalid lines are skipped and reported in the response.

### List logs (filters and pagination)

```
GET /api/v1/logs?level=error&source=auth-service&start=2026-06-20T00:00:00&end=2026-06-21T00:00:00&page=1&page_size=20
```

Query parameters (all optional):

| Param | Description |
|-------|-------------|
| `level` | Filter by level (`info`, `warn`, `error`) |
| `source` | Filter by source |
| `start` | Only entries with timestamp greater than or equal to this value |
| `end` | Only entries with timestamp less than or equal to this value |
| `page` | Page number (default `1`) |
| `page_size` | Items per page (default `20`, max `100`) |

Results are ordered by timestamp descending and include pagination metadata.

### Summarize logs

```
GET /api/v1/logs/summary?source=auth-service&start=2026-06-20T00:00:00&end=2026-06-21T00:00:00&top_errors=5
```

Returns counts by level, the most frequent error messages and the time window
covered by the matching entries. Query parameters (all optional):

| Param | Description |
|-------|-------------|
| `source` | Filter by source |
| `start` | Only entries with timestamp greater than or equal to this value |
| `end` | Only entries with timestamp less than or equal to this value |
| `top_errors` | Number of top error messages to return (default `5`, max `50`) |

### Alert rules

Create a rule (triggers when a level reaches a threshold within a time window):

```
POST /api/v1/alerts
Content-Type: application/json

{ "level": "error", "threshold": 5, "window_minutes": 10 }
```

List rules:

```
GET /api/v1/alerts
```

Evaluate which rules are currently triggered:

```
GET /api/v1/alerts/triggered
```

The evaluation counts entries per level inside each rule's window. The reference
time defaults to the latest log timestamp and can be overridden with `?at=<date-time>`.

Evaluate and deliver triggered alerts to the configured webhook:

```
POST /api/v1/alerts/notify
```

When `LOGLENS_ALERT_WEBHOOK_URL` is set and there are triggered alerts, the
evaluation payload is delivered to that URL via HTTP POST. The response reports
whether it was `delivered`. A delivery failure returns `502`.

## Seed example data

```bash
python scripts/seed.py
```

## Development

```bash
make lint      # ruff check
make format    # ruff format
make type      # mypy
make test      # pytest
make coverage  # pytest with coverage report (fails under 95%)
make check     # lint + type + test
```

The test suite covers the API endpoints, services, repositories and edge cases,
and coverage is enforced at a minimum of 95% (`pytest --cov=app`).

## Project structure

```
app/
  __init__.py        # application factory
  config.py          # environment-based settings
  extensions.py      # db, limiter, redis and Swagger setup
  errors.py          # consistent error handling
  logging_config.py  # structured logging
  api/
    health.py        # health check endpoint
    v1/              # versioned API (/api/v1)
  core/              # auth, validation, caching and file uploads
  models/            # SQLAlchemy models (LogEntry, AlertRule)
  schemas/           # Pydantic schemas
  repositories/      # data access layer
  services/          # business logic (parsing, ingestion, summary, alerts)
  observability/     # Prometheus metrics
migrations/          # Alembic migrations
seeds/               # example log file
scripts/             # helper scripts (seed)
tests/               # PyTest suite
docker-compose.yml   # PostgreSQL and Redis services
wsgi.py              # WSGI entrypoint
```
