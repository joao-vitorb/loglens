FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini wsgi.py ./
COPY docker/entrypoint.sh ./entrypoint.sh

RUN pip install --no-cache-dir ".[prod]" \
    && chmod +x entrypoint.sh \
    && useradd --create-home appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

ENTRYPOINT ["./entrypoint.sh"]
