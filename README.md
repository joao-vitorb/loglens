# LogLens

REST microservice for log analysis. It ingests logs (JSON or file upload),
parses the entries and returns summaries and alerts: counts by level, top
errors, occurrences per time window and threshold-based alerts.

## Tech stack

- Python 3.12
- Flask (blueprints)
- SQLAlchemy + Flask-SQLAlchemy
- Alembic (database migrations)
- PostgreSQL (SQLite for local development and tests)
- Pydantic / pydantic-settings
- structlog (structured logging)
- flasgger (Swagger UI)
- Ruff, mypy, pre-commit
- PyTest

## Requirements

- Python 3.12 or newer

## Setup

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

For PostgreSQL via Docker:

```
LOGLENS_DATABASE_URL=postgresql+psycopg://loglens:loglens@localhost:5432/loglens
```

## Database

Start PostgreSQL with Docker:

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

## Seed example data

```bash
python scripts/seed.py
```

## Development

```bash
make lint     # ruff check
make format   # ruff format
make type     # mypy
make test     # pytest
make check    # lint + type + test
```

## Project structure

```
app/
  __init__.py        # application factory
  config.py          # environment-based settings
  extensions.py      # Swagger setup
  errors.py          # consistent error handling
  logging_config.py  # structured logging
  api/
    health.py        # health check endpoint
    v1/              # versioned API (/api/v1)
  core/              # request and file upload validation
  models/            # SQLAlchemy models (LogEntry, AlertRule)
  schemas/           # Pydantic schemas
  repositories/      # data access layer
  services/          # business logic (parsing, ingestion)
migrations/          # Alembic migrations
seeds/               # example log file
scripts/             # helper scripts (seed)
tests/               # PyTest suite
docker-compose.yml   # PostgreSQL service
wsgi.py              # WSGI entrypoint
```
