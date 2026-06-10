setup:
	uv sync
	uv run pre-commit install

fmt:
	uv run ruff format .
	uv run ruff check . --fix

test:
	uv run pytest -q
