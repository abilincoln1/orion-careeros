# Coding Standards

## Python (backend, platform kernel)
- Python 3.10+ syntax. Type hints on all public function signatures.
- FastAPI dependency injection (`Depends(...)`) for anything request-
  scoped (DB sessions, current user) -- never module-level globals
  accessed directly inside a route handler.
- SQLAlchemy 2.0 declarative style (`Mapped[...]`, `mapped_column`), async
  engine/session throughout the request path; Alembic migrations use the
  sync driver deliberately (see ADR 0001) -- do not attempt to make
  migrations async.
- Settings are Pydantic (`pydantic-settings`) classes, never raw
  `os.environ.get()` calls scattered through the codebase.
- Every module gets a module-level docstring explaining *why* it exists,
  not just what it contains -- this repository treats that docstring as
  part of the documentation deliverable, not decoration.

## TypeScript / React (frontend)
- Strict TypeScript (`strict: true` in `tsconfig.json` -- do not weaken
  this to silence errors; fix the type instead).
- Functional components with hooks; no class components.
- API calls go through a typed client module (`src/api/*.ts`), never
  inline `fetch()` calls scattered through components.

## Naming
- Product-agnostic code lives in `orion_kernel.*` and must not import
  anything from `app.*` (a product package). This direction is one-way:
  products depend on the kernel, never the reverse.
- Names describe responsibility, not implementation detail that might
  change (`check_database_connection`, not `run_select_1_query`).

## Testing
- `pytest` + `pytest-asyncio` for the backend; async test functions use
  `@pytest.mark.asyncio` (or the auto mode configured in `pytest.ini`).
- Tests default to in-memory SQLite for speed; anything that depends on
  Postgres-specific behavior must be called out and additionally verified
  against real Postgres (see `scripts/run_tests_postgres.sh`).
