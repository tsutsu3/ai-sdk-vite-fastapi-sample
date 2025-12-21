# Repository Overview

Purpose: Provide a quick orientation for engineers working in this repo, with pointers to deeper architecture and development docs.

## Scope

- What this repository is and how to run it locally.
- High-level components (frontend, backend) and their responsibilities.
- Links to architecture and development guides.

## Non-scope

- Detailed internal design (see architecture docs).
- Step-by-step contribution workflow (see develop.md).

## What this repo contains

- Frontend: React + Vite SPA for chat UI (`frontend/`).
- Backend: FastAPI service for chat streaming, conversations, messages, and file uploads (`backend/`).
- Local storage for development (when enabled): `backend/.local-data/`.

## Quick start (local)

1. Install dependencies
   - Frontend: `pnpm install`
   - Backend: `python -m venv .venv` and install `backend/` requirements (see `backend/` setup)
2. Run backend (FastAPI) and frontend (Vite) in dev mode.
3. Open the frontend in the browser; it calls the backend under `/api`.

## Key directories

- `frontend/`: React UI, hooks, and components.
- `backend/`: FastAPI app, feature modules, and storage backends.
- `docs/`: Architecture and development documentation.

## Documentation map

- Overall architecture: `docs/architecture.md`
- Frontend internal architecture: `docs/architecture-front.md`
- Backend internal architecture: `docs/architecture-back.md`
- Development workflow: `docs/develop.md`
