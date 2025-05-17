docs: fmt
    yek shgod *.py *.md > docs/llms.txt

test: fmt
    uv run pytest --cov shgod --cov-report term

lint: fmt
    uv run ruff check --fix .

fmt:
    uv run ruff format --preview .

clean:
    rm -f .coverage
    rm -f coverage.json
    rm -f pytest.json
    rm -rf .hypothesis/
    rm -rf .ruff_cache/
    rm -rf .pytest_cache/
    rm -rf htmlcov/
