# LogLens

REST microservice for log analysis. It ingests logs (JSON or file upload),
parses the entries and returns summaries and alerts: counts by level, top
errors, occurrences per time window and threshold-based alerts.

## Tech stack

- Python 3.12
- Flask (blueprints)
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

## Running

```bash
flask --app wsgi run --debug
```

The API will be available at `http://localhost:5000`.

- Health check: `GET /health`
- API docs (Swagger UI): `GET /docs`

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
tests/               # PyTest suite
wsgi.py              # WSGI entrypoint
```
