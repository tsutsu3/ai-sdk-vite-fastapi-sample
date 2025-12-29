# Development Workflow

Purpose: Document local development workflow, conventions, and contribution practices.

## Scope

- Local setup and run steps.
- Testing and validation.
- Code organization and common workflows.

## Non-scope

- Architecture design rationale (see architecture docs).
- Production deployment runbooks.

## Prerequisites

- Node.js + pnpm for frontend.
- Python 3.x for backend.
- Optional: Docker if you use containers.

## Local setup

1. Frontend
   - `pnpm install`
   - `pnpm dev` (from `frontend/`)
2. Backend
   - Create venv and install backend deps
   - Run FastAPI app (see `backend/` instructions)

## Configuration

- Backend uses environment variables for storage backend and providers.
- Local persistence is stored under `backend/.local-data/` when `DB_BACKEND=local`.

## Common tasks

- Run frontend: `pnpm dev`
- Run backend: `uvicorn app.main:app --reload`
- Update translations: edit `frontend/src/i18n/locales/*/translation.json`
- Update backend lock file: `pip-compile pyproject.toml -o requirements.lock` (from `backend/`)

## Testing & checks

- Add tests where behavior changes.
- Run lints/formatters if configured for the project.

## Contribution notes

- Keep UI copy in i18n files.
- Prefer small, focused changes.
- Update docs when public behavior changes.
