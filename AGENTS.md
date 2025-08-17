# AGENTS.md

This document provides coding and workflow guidelines for agents working in this repository.

## Build, Lint, and Test

- Install dependencies: `uv sync`
- Run all tests: `uv run pytest`
- Run a single test file: `uv run pytest tests/enrich/test_transactions.py`
- Run a single test function: `uv run pytest tests/enrich/test_transactions.py::test_function_name`
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Type check: `uv run mypy src`

## Code Style

- **Imports**: Use absolute imports from `src/mev_tools_py`. Group as stdlib, third-party, local.
- **Formatting**: Enforced by `ruff format` (PEP8 + Black-like).
- **Types**: All public functions and methods must be type-annotated. Use `mypy` to validate.
- **Naming**:
  - Modules: `snake_case`
  - Classes: `PascalCase`
  - Functions/variables: `snake_case`
  - Constants: `UPPER_CASE`
- **Error Handling**: Raise specific exceptions, avoid bare `except`. Log or re-raise with context.
- **Tests**: Use `pytest`. Place under `tests/` mirroring `src/` structure.
- **Commits/PRs**: Keep changes small, with clear commit messages. Ensure lint, type, and tests pass.
