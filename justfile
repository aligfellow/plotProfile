# Run all checks
check: lint type test

lint:
    uv run ruff format .
    uv run ruff check .

type:
    uv run ty check

test:
    uv run python -m pytest --cov --cov-report=xml -v

fix:
    uv run ruff format .
    uv run ruff check --fix .

build:
    uv build

# Build the docs; -W fails the build on a broken link or missing image
docs:
    uv run --with-requirements docs/requirements.txt sphinx-build -W -b html docs/source docs/_build/html
    @echo "docs/_build/html/index.html"

# Rebuild and reload in the browser on every save
docs-serve:
    uv run --with-requirements docs/requirements.txt --with sphinx-autobuild \
        sphinx-autobuild docs/source docs/_build/html --open-browser

setup:
    uv sync --dev
    uv run pre-commit install
