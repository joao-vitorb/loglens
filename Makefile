.PHONY: install run lint format type test check

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

test:
	pytest

check: lint type test
