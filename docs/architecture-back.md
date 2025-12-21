# Backend Architecture

Purpose: Describe the internal structure of the FastAPI backend, services, and storage.

## Scope

- API modules and core services.
- Storage backends and responsibilities.
- Streaming and title generation flow.

## Non-scope

- Frontend internals (see `architecture-front.md`).
- Deployment/infrastructure specifics.

## High-level structure

- FastAPI app in `backend/app`.
- Feature modules under `backend/app/features`.
- Repositories for conversation/message/usage storage.
- Streamers for chat providers (memory, azure, ollama).

```mermaid
flowchart TD
  Router[FastAPI Routers] --> RunService
  Router --> ConversationService
  Router --> MessageRepo
  RunService --> Streamer[Chat Streamers]
  RunService --> TitleGen[Title Generator]
  RunService --> Repos[Conversation/Message/Usage Repos]
  Repos --> Storage[Memory/Local/Azure]
```

## Core modules

- `features/run`: orchestrates chat streaming and persistence.
- `features/conversations`: list/update/archive/delete conversation metadata.
- `features/messages`: store and fetch message history.
- `features/chat/streamers`: provider-specific streaming implementation.
- `features/title`: title generation (model or fallback).

## Storage backends

- `memory`: in-process store (non-persistent).
- `local`: JSON files under `backend/.local-data/`.
- `azure`: Cosmos DB + blob storage (when configured).

## Streaming flow

1. `/api/chat` receives a message payload.
2. `RunService` prepares conversation, persists input messages.
3. `Streamer` streams assistant response (SSE data protocol).
4. Title is generated asynchronously and persisted.
5. Usage is recorded.

## APIs served by backend

- `/api/chat` (streaming)
- `/api/conversations` (list, archive all, delete all)
- `/api/conversations/{id}` (patch, delete)
- `/api/conversations/{id}/messages`
- `/api/file` (blob upload)
- `/api/capabilities`, `/api/authz`, `/health`

