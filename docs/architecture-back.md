# Backend Architecture

Purpose: Describe the internal structure of the FastAPI backend, services, and storage.

## Scope

- API routes and core services.
- Storage backends and responsibilities.
- Streaming and title generation flow.

## Non-scope

- Frontend internals (see `architecture-front.md`).
- Deployment/infrastructure specifics.

## High-level structure

- FastAPI entrypoint in `backend/app/main.py`, with app factory and lifespan in
  `backend/app/core/application.py`.
- `app/core`: app bootstrap, config, middleware, telemetry, dependencies.
- `app/features`: feature modules; each has `routes.py`, `schemas.py`, `models.py`, `ports.py`, optional `service.py`.
- `app/ai`: LangChain chains, LLM/embeddings factories, retrievers, chat history.
- `app/infra`: storage clients, repositories, cache providers, blob storage, usage buffer.
- `app/shared`: cross-cutting constants, exceptions, ports (e.g., `BlobStorage`).

The backend separates HTTP routing, domain services, and storage backends. Feature
modules own request/response schemas and domain models, while `infra/` contains
backend-specific adapters (Cosmos, Firestore, local, memory). The app bootstrap wires
adapters into `app.state` (config, capabilities, repositories, caches, blob storage,
runtime services) and endpoints depend on those interfaces via `Depends(...)`.

```mermaid
flowchart TD
  Router[Feature Routers] --> RunService
  Router --> ConversationService
  Router --> MessageRepo
  RunService --> Streamer[Chat Streamers]
  RunService --> TitleGen[Title Generator]
  RunService --> Repos[Conversation/Message/Usage Repos]
  Repos --> Storage[shared/infra backends]
```

## Module interaction map

```mermaid
flowchart LR
  subgraph API[Feature Routers]
    Chat[/api/chat/]
    Convos[/api/conversations/]
    Messages["/api/conversations/{id}/messages/"]
    Authz[/api/authz/]
  end

  subgraph Services[Services]
    RunService
    ConversationService
  end

  subgraph Repos[Repository Interfaces]
    AuthzRepo
    ConversationRepo
    MessageRepo
    UsageRepo
  end

  subgraph Infra[Infra Implementations]
    Streamers
    Storage[(Memory/Local/Cosmos/Blob)]
  end

  Chat --> RunService
  Convos --> ConversationService
  Messages --> MessageRepo
  Authz --> AuthzRepo

  RunService --> Streamers
  RunService --> ConversationRepo
  RunService --> MessageRepo
  RunService --> UsageRepo
  ConversationService --> ConversationRepo
  ConversationService --> MessageRepo

  AuthzRepo --> Storage
  ConversationRepo --> Storage
  MessageRepo --> Storage
  UsageRepo --> Storage
```

The module map emphasizes that routers never talk to storage directly. They only
call services or repository interfaces, and concrete storage implementations live
under `infra/`.

## Core modules

- `features/run`: orchestrates chat streaming and persistence.
- `features/conversations`: list/update/archive/delete conversation metadata.
- `features/messages`: store and fetch message history.
- `features/run/streamers`: AI SDK streaming adapters (memory or LangChain).
- `features/title`: title generation helpers.
- `features/authz`: tenant/user authorization resolution and tool access.
- `features/retrieval`: RAG query orchestration and streaming.
- `features/file`: blob upload/download endpoints.
- `features/capabilities`, `features/health`: support endpoints.
- `features/*/routes.py`: FastAPI routers per feature.

## Storage backends

- `memory`: in-process store (non-persistent).
- `local`: JSON files under `backend/.local-data/`.
- `azure`: Cosmos DB + Azure Blob (when configured).
- `gcp`: Firestore + GCS (when configured).

Storage implementations live in `backend/app/infra/{repository,storage}`.
Cache providers are selected via `app_config.cache_backend` (`memory`, `redis`, `off`)
and wrap authz/messages repositories.
Usage logs are buffered via `infra/storage/usage_buffer.py` with `off | local | azure | gcp`
backends.

## Authorization data flow

- `AuthzContextMiddleware` resolves authz context for most `/api/*` routes.
- `request_context.resolve_request_context` uses `AuthzService.resolve_access` to:
  - look up `UserIdentity` → `User` → `Tenant`, or
  - provision a new user from a `ProvisioningRecord` if eligible.
- `CachedAuthzRepository` wraps the backing repository with TTL caching.
- Effective tools are computed by merging tenant defaults with user overrides.

## Blob storage contracts

- `shared/ports/blob_storage.py` defines the `BlobStorage` contract used by features.
- `infra/storage/*` implements Azure/Local/Memory backends.
- `get_object_url` returns a URL for blob access; local/memory use `/api/file/{id}/download`.

## Message/conversation models

- API payloads live in `features/*/schemas.py`, domain models in `features/*/models.py`.
- Message payloads are normalized into Pydantic models (`ChatMessage`, `MessagePart`).
- Local storage persists models as JSON; Cosmos stores per-message documents with a `message` payload.

## Tenant scoping

- Tenant resolution happens per request and is stored in request context.
- Service-layer code uses tenant-scoped adapters to keep infra repositories request-agnostic.

## Dependency injection flow

```mermaid
flowchart TD
  App[FastAPI app startup] --> State[app.state.* registrations]
  State --> AuthzRepo[authz_repository]
  State --> ConversationRepo[conversation_repository]
  State --> MessageRepo[message_repository]
  State --> UsageRepo[usage_repository]
  State --> RunService[run_service]

  Request[HTTP request] --> Middleware[AuthzContextMiddleware]
  Middleware --> AuthzService
  AuthzService --> AuthzRepo
  Request --> Router[Feature router]
  Router --> Depends["Depends resolution"]
  Depends --> State
  Router --> Handler[Endpoint handler]
  Handler --> RunService
  Handler --> ConversationRepo
  Handler --> MessageRepo
  Handler --> UsageRepo
```

Dependencies are resolved via `Depends(...)` and read from `app.state`. This keeps
handlers testable while allowing storage backends to be swapped at startup.

## Access control flow

```mermaid
sequenceDiagram
  participant Client
  participant Router as Feature Router
  participant Middleware as AuthzContextMiddleware
  participant AuthzSvc as AuthzService
  participant AuthzRepo as AuthzRepository
  participant Service
  participant Repo

  Client->>Router: Request
  Router->>Middleware: request passes middleware
  Middleware->>AuthzSvc: resolve_access(user)
  AuthzSvc->>AuthzRepo: get_user_identity/get_user/get_tenant
  AuthzRepo-->>AuthzSvc: authz records
  Middleware-->>Router: set request context
  Router->>Service: call handler/service
  Service->>Repo: repo methods (tenant scoped)
  Repo-->>Service: data
  Service-->>Router: response
  Router-->>Client: response
```

Access control happens in `AuthzContextMiddleware`, which resolves the user identity
and authz record before any handler runs. Handlers then use tenant-scoped repositories
so tenant_id does not leak into the routing layer.

## Streaming flow

1. `/api/chat` receives a message payload.
2. `RunService` prepares conversation, persists input messages.
3. `ChatRuntime` streams assistant response (optionally with retrieval system prompt).
4. `Streamer` emits AI SDK events (`start`, `text-start`, `text-delta`, `text-end`).
5. Title is generated asynchronously and emitted via `data.title`.
6. Usage is recorded.

### SSE data events

The stream includes typed `data-*` events for client-side orchestration:

- `data-conversation`: conversation id for route updates.
- `data-title`: conversation title for history updates.
- `data-model`: model id used for a message (UI metadata).

When `tool_id` is present, the stream also emits `reasoning-*` events with retrieval
tool/query metadata.

These events are emitted by the streaming pipeline so the frontend can update
route state and metadata without polling.

## LangChain chat + RAG flow (request to stream)

This flow describes how LangChain is used to build prompts, retrieval context, and
streamed responses for chat and RAG endpoints.

```mermaid
sequenceDiagram
  participant Client
  participant Router as /api/chat or /api/rag/query
  participant RunService
  participant RetrieverFactory as ai/retrievers/factory.py
  participant ChatRuntime
  participant LangChain as LangChain chain/LLM
  participant MessageRepo
  participant ConversationRepo
  participant UsageRepo

  Client->>Router: request
  Router->>RunService: prepare stream context
  RunService->>ConversationRepo: upsert conversation
  RunService->>MessageRepo: list messages
  alt RAG (/api/rag/query)
    RunService->>RetrieverFactory: build retriever
    RetrieverFactory-->>RunService: retriever + docs
  end
  RunService->>ChatRuntime: stream_text / stream_text_with_system
  ChatRuntime->>LangChain: build prompt + history
  LangChain-->>ChatRuntime: token deltas
  ChatRuntime-->>RunService: deltas
  RunService-->>Router: AI SDK events (start/text/data/...)
  RunService->>MessageRepo: upsert messages
  RunService->>ConversationRepo: update title
  RunService->>UsageRepo: record usage
  Router-->>Client: SSE stream
```

Notes:
- Chat uses LangChain message history + prompt template.
- RAG adds a system prompt built from retrieved documents, and emits RAG-specific
  data events (`data.rag`, `data.sources`, `data.cot`).

## LangChain conversation, persistence, and memory flow

This flow highlights how stored messages are reused as memory and persisted
throughout a LangChain-backed chat run.

```mermaid
flowchart TD
  Request[/api/chat/] --> RunService
  RunService -->|list_messages| MessageRepo
  RunService -->|upsert_conversation| ConversationRepo
  RunService --> ChatRuntime
  ChatRuntime -->|RunnableWithMessageHistory| LangChainHistory[LangChain history]
  LangChainHistory -->|load| HistoryFactory[history factory]
  HistoryFactory --> MessageRepo
  ChatRuntime -->|stream_text| LLM[LangChain LLM]
  LLM --> ChatRuntime
  ChatRuntime --> RunService
  RunService -->|upsert_messages| MessageRepo
  RunService -->|update title| ConversationRepo
  RunService -->|record usage| UsageRepo
```

Notes:
- Message history is fetched from the repository and provided to LangChain as
  conversation memory.
- The assistant response is persisted as message parts after the stream completes.
- Titles and usage are persisted alongside the message update.

## Retrieval (RAG) flow

1. `/api/rag/query` receives tool/provider parameters and chat history.
2. Tool specs are loaded at startup from `retrieval_tools.yaml`.
3. Request context validates tenant/tool access and resolves provider/data source.
4. Retriever is built via `ai/retrievers/factory.py` (`memory`, `local-files`, `ai-search`,
   `vertex-search`, `vertex-answer`).
5. Results are streamed with AI SDK events (`start`, `data.conversation`, `data.cot`,
   `data.rag`, `data.sources`, `source-url`, `text-*`, `data.title`).
6. Usage is recorded; conversations are upserted and titled as needed.

### Retrieval mode behavior

- `simple`: search_query = user_query, question = user_query.
- `chat`: if `tool.query_prompt` exists, generate search_query from history + last user message.
- `answer`: force provider `vertex-answer`; answer text comes from answer documents (no LLM).

```mermaid
flowchart TD
  Request[Request /api/rag/query] --> Mode[Resolve mode]
  Mode -->|simple| Simple[search_query = user_query]
  Mode -->|chat + query_prompt| Chat[LLM generates search_query from history + user]
  Mode -->|answer| Answer[provider = vertex-answer]
  Simple --> Retrieve[Retrieve documents]
  Chat --> Retrieve
  Answer --> Retrieve
  Retrieve --> Response[Stream response + events]
```

Notes:
- `query_prompt` only affects search_query generation; it does not replace the answer question.
- `answer` mode bypasses LLM generation and returns answer docs directly.

### HyDE flow

HyDE (Hypothetical Document Embeddings) inserts a "hypothetical answer" generation
step before retrieval to improve search relevance. It is toggled by `hydeEnabled`
in the retrieval request payload.

```mermaid
flowchart TD
  User[User query + history] --> Hypo[Generate hypothetical answer (HyDE)]
  Hypo --> SearchQuery[Derive search query from hypothetical answer]
  SearchQuery --> Retrieve[Retrieve documents]
  Retrieve --> Answer[Generate final answer]
```

Behavior:
- HyDE is optional (toggle) and does not change event order or payload shape.
- When disabled, the flow remains identical to `simple` / `chat` mode behavior.

## API responsibilities and boundaries

- Routers validate input/output and delegate to services.
- Services orchestrate streaming, persistence, and usage logging.
- Repositories abstract storage access; infra implementations handle the backend.

This keeps HTTP concerns separate from domain logic and storage concerns, making
feature-level changes (streaming, title, usage) localized to services.

## APIs served by backend

- `/api/chat` (streaming)
- `/api/rag/query` (streaming retrieval)
- `/api/conversations` (list, archive all, delete all)
- `/api/conversations/{id}` (patch, delete)
- `/api/conversations/{id}/messages` (list)
- `/api/conversations/{id}/messages/{message_id}` (reaction)
- `/api/file` (upload)
- `/api/file/{id}/download` (download)
- `/api/capabilities`, `/api/authz`, `/health`

## Tests

- `backend/tests/unit`: unit tests for services and helpers.
- `backend/tests/integration`: integration tests against storage adapters.
- `backend/tests/contract`: API contract/response shape tests.
