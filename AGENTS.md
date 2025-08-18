# AGENTS.md

This document provides coding and workflow guidelines for agents working in this repository.

## Build, Lint, and Test

### Task Runner (Poethepoet)

This project uses [poethepoet](https://poethepoet.natn.io/) as a task runner. All common development tasks are available via `poe` commands:

**Development Workflow:**
- Install dependencies: `uv run poe install` (or `uv sync`)
- Full development setup: `uv run poe dev` (installs, formats, lints, type-checks, and tests)
- Run pre-commit checks: `uv run poe pre-commit`

**Testing:**
- Run all tests: `uv run poe test`
- Run tests with coverage report: `uv run poe coverage`
- Run tests in watch mode: `uv run poe test-watch`
- Run verbose tests: `uv run poe test-verbose`
- Run a specific test file: `uv run poe test-file tests/enrich/test_transactions.py`
- Run a specific test function: `uv run poe test-function --file tests/enrich/test_transactions.py --function test_function_name`

**Code Quality:**
- Lint: `uv run poe lint`
- Auto-fix linting issues: `uv run poe lint-fix`
- Format: `uv run poe format`
- Check formatting: `uv run poe format-check`
- Type check: `uv run poe typecheck`
- Run all quality checks: `uv run poe check`
- Auto-fix style issues: `uv run poe fix`

**Build and Clean:**
- Clean cache files: `uv run poe clean`
- Build package: `uv run poe build`
- Clean and build: `uv run poe publish`

**Legacy Commands (still work):**
- Install dependencies: `uv sync`
- Run all tests: `uv run pytest`
- Run a single test file: `uv run pytest tests/enrich/test_transactions.py`
- Run a single test function: `uv run pytest tests/enrich/test_transactions.py::test_function_name`
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Type check: `uv run mypy src`

### Changelog Management

This project uses [Commitizen](https://commitizen-tools.github.io/commitizen/) for changelog management and conventional commits:

**Commit with conventional format:**
```bash
cz commit  # Interactive commit with conventional format
# or use git with conventional format manually:
git commit -m "feat(auth): add OAuth2 integration"
```

**Release management:**
```bash
cz bump          # Auto-bump version and update changelog
cz changelog     # Generate changelog only
cz version -p    # Show current version
```

**Conventional commit types:**
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

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
