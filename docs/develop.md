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

## OpenAI / Azure OpenAI

- This backend uses **Azure OpenAI** for production chat models.
- Required settings (when using Azure):
  - `AZURE_OPENAI_ENDPOINT`
  - `AZURE_OPENAI_API_KEY`
  - `AZURE_OPENAI_API_VERSION`
  - `AZURE_OPENAI_DEPLOYMENTS` (map of model id → deployment name)
  - `CHAT_DEFAULT_MODEL` / `CHAT_TITLE_MODEL`
- For local/test, prefer `memory` or `ollama` providers and avoid real cloud calls by default.

## Firestore indexes (DB_BACKEND=gcp)

Firestore queries in this project require composite indexes. Create them in the
Firebase/Firestore console if you see index errors.

Recommended indexes:
- `conversations`: tenantId + userId + archived + updatedAt (desc) + id (desc)
- `messages`: tenantId + userId + conversationId + createdAt (asc/desc) + id (asc/desc)
- `provisioning`: email + status

## Common tasks

- Run frontend: `pnpm dev`
- Run backend: `uvicorn app.main:app --reload` or `pnpm dev`
  - with specific .env args `pnpm dev -- --env-file .env.local`
- Update translations: edit `frontend/src/i18n/locales/*/translation.json`
- Update backend lock file: `pip-compile pyproject.toml -o requirements.lock` (from `backend/`)

## Testing & checks

- Add tests where behavior changes.
- Run lints/formatters if configured for the project.
- Test layers:
  - **contract**: API response shape/compatibility (`backend/tests/contract`)
  - **integration**: end-to-end flows with repositories/streaming (`backend/tests/integration`)
  - **unit**: isolated logic for services/repos (`backend/tests/unit`)
- Recommended:
  - `pnpm --dir backend test` (full)
  - `pnpm --dir backend test -- tests/contract tests/integration` (API focus)

## Contribution notes

- Keep UI copy in i18n files.
- Prefer small, focused changes.
- Update docs when public behavior changes.
