.PHONY: install run lint format type seed test coverage check

install:
	pip install -e ".[dev]"

run:
	flask --app wsgi run --debug

lint:
	ruff check .

format:
	ruff format .

type:
	mypy

seed:
	python scripts/seed.py

test:
	pytest

coverage:
	pytest --cov=app

check: lint type test
