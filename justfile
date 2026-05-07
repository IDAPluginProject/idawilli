set quiet

format:
    uvx --quiet ruff format --quiet idawilli/ scripts/ plugins/ tests/ tools/

ruff:
    uvx --quiet ruff check --quiet --fix idawilli/ scripts/ plugins/ tests/ tools/
    uvx --quiet ruff check --quiet --select I --fix idawilli/ scripts/ plugins/ tests/ tools/

mypy:
    uv run --quiet mypy --no-error-summary ./idawilli ./scripts ./plugins ./tests ./tools

test:
    uv run --quiet pytest -x -q --no-header

lint: format ruff mypy
