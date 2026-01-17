import asyncio
import random
import time
from collections.abc import AsyncIterator, Iterator

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult

_text01 = """
Below is a **detailed, practical guide to React Hooks**, from fundamentals to advanced patterns. It’s written to be used as a reference, not just a tutorial.

---

# React Hooks Guide (Detailed)

## 1. What Are Hooks?

**Hooks** are functions that let you use React features (state, lifecycle, context, etc.) in **function components**.

Before Hooks:

* State & lifecycle → **class components**
* Logic reuse → **HOCs / render props** (often complex)

With Hooks:

* State & effects → **function components**
* Logic reuse → **custom hooks**
* Less boilerplate, clearer composition

---

## 2. Rules of Hooks (Very Important)

Hooks **must** follow these rules:

1. **Only call Hooks at the top level**

   ```tsx
   // ❌ Wrong
   if (condition) {
     useEffect(...)
   }
   ```

2. **Only call Hooks from React functions**

   * Function components
   * Custom hooks

React relies on **call order**, not names.

---

## 3. `useState`

### Basic usage

```tsx
const [count, setCount] = useState(0)
```

### Functional updates (important)

Use when next state depends on previous state:

```tsx
setCount(prev => prev + 1)
```

### Object state (don’t forget immutability)

```tsx
const [user, setUser] = useState({ name: '', age: 0 })

setUser(prev => ({
  ...prev,
  age: prev.age + 1,
}))
```

❌ React does **not** merge objects automatically.

---

## 4. `useEffect`

Handles **side effects**:

* Data fetching
* Subscriptions
* Timers
* DOM manipulation

### Basic effect

```tsx
useEffect(() => {
  console.log('Mounted')
}, [])
```

### Dependency array behavior

| Dependency array | When it runs            |
| ---------------- | ----------------------- |
| none             | Every render            |
| `[]`             | Once (mount)            |
| `[a, b]`         | When `a` or `b` changes |

### Cleanup

```tsx
useEffect(() => {
  const id = setInterval(() => {}, 1000)

  return () => clearInterval(id)
}, [])
```

Cleanup runs:

* Before re-running the effect
* On unmount

---

## 5. `useContext`

Avoids **prop drilling**.

### Creating context

```tsx
const ThemeContext = createContext<'light' | 'dark'>('light')
```

### Providing

```tsx
<ThemeContext.Provider value="dark">
  <App />
</ThemeContext.Provider>
```

### Consuming

```tsx
const theme = useContext(ThemeContext)
```

Best practice:

* Combine with custom hooks

```tsx
function useTheme() {
  return useContext(ThemeContext)
}
```

---

## 6. `useRef`

### Persistent mutable value (no re-render)

```tsx
const countRef = useRef(0)
countRef.current += 1
```

### Accessing DOM elements

```tsx
const inputRef = useRef<HTMLInputElement>(null)

<input ref={inputRef} />

inputRef.current?.focus()
```

**Key difference:**

* `useState` → causes re-render
* `useRef` → does NOT cause re-render

---

## 7. `useMemo`

Memoizes **computed values**.

```tsx
const expensiveValue = useMemo(() => {
  return heavyCalculation(data)
}, [data])
```

Use when:

* Calculation is expensive
* Referential equality matters

❌ Don’t use for everything — it adds complexity.

---

## 8. `useCallback`

Memoizes **functions**.

```tsx
const handleClick = useCallback(() => {
  setCount(c => c + 1)
}, [])
```

Useful when:

* Passing callbacks to memoized child components
* Preventing unnecessary re-renders

---

## 9. `React.memo` + Hooks

```tsx
const Child = React.memo(({ onClick }) => {
  return <button onClick={onClick}>Click</button>
})
```

Combine with `useCallback`:

```tsx
const onClick = useCallback(() => {
  ...
}, [])
```

Otherwise `memo` is useless.

---

## 10. `useReducer`

Best for **complex state logic**.

```tsx
type State = { count: number }
type Action = { type: 'inc' | 'dec' }

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'inc':
      return { count: state.count + 1 }
    case 'dec':
      return { count: state.count - 1 }
  }
}
```

```tsx
const [state, dispatch] = useReducer(reducer, { count: 0 })
```

Benefits:

* Predictable state transitions
* Easier testing
* Redux-like pattern without Redux

---

## 11. Custom Hooks (Core Concept)

Custom hooks **extract logic**, not UI.

### Example: `useFetch`

```tsx
function useFetch<T>(url: string) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(url)
      .then(res => res.json())
      .then(setData)
      .finally(() => setLoading(false))
  }, [url])

  return { data, loading }
}
```

Usage:

```tsx
const { data, loading } = useFetch<User[]>('/api/users')
```

Custom hooks:

* Must start with `use`
* Can call other hooks
* Share logic cleanly

---

## 12. Common Pitfalls

### ❌ Missing dependencies

```tsx
useEffect(() => {
  doSomething(value)
}, []) // BUG
```

Always include dependencies or refactor.

### ❌ Overusing `useMemo` / `useCallback`

Premature optimization hurts readability.

### ❌ Storing derived state

```tsx
// ❌ Avoid
const [fullName, setFullName] = useState(first + last)
```

Instead:

```tsx
const fullName = `${first} ${last}`
```

---

## 13. Mental Model (Important)

Think in **data flow**, not lifecycle.

* Render = function execution
* Hooks = attach behavior to renders
* Effects = synchronize React with external systems

---

## 14. When to Use Which Hook

| Use case                  | Hook          |
| ------------------------- | ------------- |
| Local state               | `useState`    |
| Side effects              | `useEffect`   |
| Shared global state       | `useContext`  |
| Complex state transitions | `useReducer`  |
| Expensive calculations    | `useMemo`     |
| Stable callbacks          | `useCallback` |
| DOM / mutable value       | `useRef`      |

---

## 15. Recommended Learning Order

1. `useState`
2. `useEffect`
3. `useContext`
4. `useRef`
5. `useMemo` / `useCallback`
6. `useReducer`
7. Custom hooks

---

If you want, I can:

* Compare Hooks vs **class lifecycle methods**
* Show **real-world patterns** (forms, API, auth)
* Map Hooks concepts to **Flutter / Provider / MVVM**
* Explain **StrictMode + double rendering**

Just tell me 👍
"""

_text02 = """
Below is a production-oriented, cloud-ready reference architecture for:

* **Backend:** FastAPI + LangChain (agent/RAG/tools)
* **Frontend:** Vite + **Vercel AI SDK** (streaming, tool calls) + **ai-elements** (chat UI primitives)

I’ll keep it vendor-neutral, but I’ll note cloud options where it matters.

---

## 1) High-level system layout

**Client (Vite + AI SDK + ai-elements)**

* Chat UI, message list, tool-call rendering, file upload UI
* Talks only to **your API Gateway / FastAPI** (never directly to OpenAI/Anthropic from browser in prod unless you *really* intend to)

**API Gateway / Edge**

* TLS termination, WAF, rate limiting, request auth verification
* Routes to FastAPI “AI service” and other microservices

**FastAPI “AI Orchestrator”**

* Streaming chat endpoint (SSE recommended) compatible with AI SDK
* LangChain pipelines: RAG, tool calling, structured outputs
* Multi-tenant policy enforcement, prompt templates, safety checks
* Short-lived state (in Redis), long-lived state (DB)

**Data plane**

* Postgres: users, orgs, chat metadata, permissions, audit logs
* Vector DB: embeddings + chunks + metadata filters (pgvector, Pinecone, Weaviate, etc.)
* Object storage: raw docs, parsed text, images, attachments (S3/GCS/Azure Blob)

**Async workers**

* Ingestion: parse → chunk → embed → upsert vectors
* Long/expensive tools: web crawling, PDF parsing, OCR, batch summarization
* Queue: SQS/PubSub/Rabbit/Kafka + workers (Celery/RQ/Arq)

**Observability & governance**

* Central logs + traces + metrics (OpenTelemetry)
* LLM tracing (LangSmith / OpenTelemetry spans)
* Secrets manager + key rotation
* Audit trails for data access and model calls

---

## 2) Backend: service boundaries (practical split)

You can run these as separate services or start as a modular monolith.

### A) `ai-api` (FastAPI)

**Responsibility:** user-facing AI endpoints + orchestration

* `/v1/chat` (SSE streaming)
* `/v1/chat/tools` (optional tool registry exposure)
* `/v1/files/*` (upload → signed URL, status)
* `/v1/threads/*` (persisted chat threads)

Internals:

* `ChatController` → auth/tenant guard → `ChatService`
* `ChatService` chooses pipeline: “pure chat” vs “RAG” vs “agent”
* Uses Redis for ephemeral state (stream sessions, rate windows)

### B) `ingest-worker`

**Responsibility:** document ingestion & indexing
Pipeline:

1. Fetch file from object store
2. Parse (PDF/DOCX/HTML)
3. Clean + chunk
4. Embed
5. Upsert into vector store with metadata:

   * `tenant_id`, `doc_id`, `source`, `acl_tags`, `created_at`, `language`, etc.

### C) `tool-worker` (optional)

**Responsibility:** long-running tool calls (or tools that require VPC access)

* database analytics, ERP/CRM queries, data warehouse queries
* internal HTTP calls behind private network

---

## 3) Frontend: AI SDK + ai-elements integration pattern

**Key principle:** frontend is “thin”. It renders and streams. Backend decides prompts, tools, RAG, policies.

Recommended pattern:

* AI SDK `useChat()` points to `/v1/chat`
* Backend returns streaming tokens + structured tool events
* ai-elements renders:

  * assistant messages
  * tool call “cards” (search results, citations, tables)
  * file upload status / ingestion progress

If you want “function calling” UX:

* UI shows tool execution states
* Backend emits tool events (start/progress/end)
* UI uses a stable schema for each tool result type

---

## 4) RAG in production: what you actually need

### Retrieval stack

* **Hybrid retrieval**: vector + keyword (if possible)
* Metadata filters for multi-tenant + ACL:

  * `tenant_id = X AND (doc_acl contains user_role OR user_id)`
* Reranking (optional but huge quality boost):

  * cross-encoder reranker or LLM-based rerank for top 20–50

### Ingestion requirements

* Deduping + versioning
* Chunk IDs stable across re-index
* Backpressure & retries
* Incremental indexing per tenant

### Citation support

Store chunk metadata and return citations:

* `doc_title`, `source_url`, `page`, `chunk_id`
  Then the UI can show “Sources” with deep links.

---

## 5) Streaming + reliability (the stuff that breaks in prod)

### Streaming transport

* **SSE** is simplest with FastAPI and plays nicely with proxies
* Make sure your load balancer / gateway supports:

  * long-lived connections
  * disabled response buffering (or explicit flush)
  * timeouts tuned (60–300s depending on use)

### Idempotency & retries

* Client sends `idempotency_key` per user message
* Backend stores last completion status in Redis/DB
* If client reconnects, backend can resume or restart safely

### Rate limiting

Rate limit by:

* user_id, tenant_id, IP
* “token budget” per minute (approx) to prevent runaway costs

### Fallbacks

* If a model times out, fall back to a cheaper/faster model
* If vector store is down, degrade to “no-RAG mode” with a warning

---

## 6) Security & tenancy checklist

**Auth**

* OIDC (Auth0/Cognito/Entra/Keycloak) → JWT verification at gateway + FastAPI

**Tenant isolation**

* Always attach `tenant_id` from token claims server-side
* Never trust client-provided tenant identifiers

**Secrets**

* Model API keys in Secrets Manager (not env in CI logs)
* Separate keys per environment and ideally per tenant (if needed)

**Data access**

* Signed URLs for uploads/downloads
* Encrypt at rest (managed KMS)
* Audit logs: who asked what, which docs were retrieved (metadata-only if needed)

---

## 7) Deployment topology (cloud-agnostic)

### Compute

* Containerize services (Docker)
* Run on:

  * Kubernetes (EKS/GKE/AKS) **or**
  * Managed container platforms (ECS/Fargate, Cloud Run, Azure Container Apps)

### Scaling

* `ai-api`: scale on CPU + concurrent requests (and keep an eye on open connections)
* workers: scale on queue depth
* vector DB: scale on query load + index size

### Networking

* Put `ai-api` behind gateway
* Put internal tools behind private network (VPC)
* Use VPC endpoints/private service access where possible

---

## 8) Observability & evaluation (don’t skip)

**Telemetry**

* OpenTelemetry traces across gateway → FastAPI → vector DB → model provider
* Correlate request id / conversation id

**LLM monitoring**

* Capture:

  * prompt template version
  * retrieval stats (top-k, scores)
  * tool calls
  * cost estimates
* Add “golden set” evaluation jobs for regressions:

  * nightly runs against canonical questions per tenant/domain

**Human review**

* For high-stakes tenants: enable sampling + redaction for privacy

---

## 9) Suggested FastAPI project structure (works well with LangChain)

```
ai-api/
  app/
    main.py
    api/
      v1/
        chat.py
        files.py
        threads.py
    core/
      config.py
      auth.py
      tenancy.py
      rate_limit.py
      logging.py
    llm/
      models.py
      prompts/
      tools/
      pipelines/
        chat_pipeline.py
        rag_pipeline.py
        agent_pipeline.py
    retrieval/
      vectorstore.py
      rerank.py
      citations.py
    persistence/
      db.py
      repositories/
    cache/
      redis.py
```

---

## 10) Minimal “production-ready” endpoint contract (AI SDK-friendly)

* `POST /v1/chat`
  Body:

  * `thread_id` (optional)
  * `messages[]` (role/content)
  * `attachments[]` (optional references)
  * `metadata` (optional)
* Response: **SSE stream**

  * token deltas
  * tool events
  * final message with citations

This maps cleanly to AI SDK streaming on the client and keeps “logic” server-side.

---

If you tell me **(a)** which cloud (AWS/GCP/Azure), **(b)** expected scale (users / req/s), and **(c)** whether you need strict data residency or multi-tenant SaaS, I can adapt this into a concrete deployment blueprint (network diagram + service sizing + exact managed services).
"""

_text03 = """
Here’s a clear, practical comparison of **FastAPI** and **Quart**, focusing on architecture, performance, ecosystem, and when to choose each.

---

## High-level overview

| Aspect            | **FastAPI**                   | **Quart**                    |
| ----------------- | ----------------------------- | ---------------------------- |
| Primary goal      | Modern, high-performance APIs | Async version of Flask       |
| Base framework    | Starlette                     | Flask-compatible             |
| Async support     | Native, first-class           | Native                       |
| Type hints        | Core feature                  | Optional                     |
| OpenAPI / Swagger | Built-in, automatic           | Manual (extensions)          |
| Performance       | Very high                     | Good                         |
| Learning curve    | Moderate                      | Low (for Flask users)        |
| Maturity          | Very active, fast-growing     | Stable but smaller ecosystem |

---

## Philosophy & design

### FastAPI

* Designed **specifically for APIs**
* Strongly opinionated around:

  * **Type hints**
  * **Pydantic models**
  * Automatic validation and serialization
* Encourages **explicit contracts** (schemas)

➡️ You write less glue code, but must follow its patterns.

### Quart

* Designed as **Flask, but async**
* Almost drop-in replacement for Flask:

  ```python
  from quart import Quart
  app = Quart(__name__)
  ```
* Minimal opinions
* Lets you structure things however you want

➡️ Maximum flexibility, minimal framework “magic”.

---

## Performance

| Area             | FastAPI                   | Quart           |
| ---------------- | ------------------------- | --------------- |
| Request handling | ⭐⭐⭐⭐⭐                     | ⭐⭐⭐⭐            |
| Validation       | Extremely fast (Pydantic) | Manual / slower |
| WebSockets       | Excellent                 | Excellent       |
| Throughput       | Generally higher          | Slightly lower  |

**Why FastAPI is faster**

* Built on **Starlette**
* Uses **Pydantic (Rust-backed validation in v2)**
* Optimized routing and dependency injection

Quart is still async and fast, but closer to Flask’s design constraints.

---

## Type safety & validation

### FastAPI (core strength)

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    return {"item_id": item_id}
```

* Automatic:

  * Input validation
  * Type coercion
  * Error responses
  * OpenAPI schema

### Quart

```python
@app.route("/items/<int:item_id>")
async def get_item(item_id):
    return {"item_id": item_id}
```

* No automatic validation for:

  * JSON bodies
  * Query parameters
* Requires:

  * Marshmallow / Pydantic / manual checks

---

## API documentation

| Feature      | FastAPI          | Quart              |
| ------------ | ---------------- | ------------------ |
| Swagger UI   | ✅ Built-in       | ❌ Extension needed |
| OpenAPI spec | ✅ Auto-generated | ❌ Manual           |
| Redoc        | ✅                | ❌                  |

FastAPI wins **by far** for API-first development.

---

## Ecosystem & extensions

### FastAPI

* Tight ecosystem around:

  * Pydantic
  * Starlette
  * SQLModel
* Strong async database support
* Excellent community momentum

### Quart

* Reuses **Flask extensions** (sometimes)
* Some Flask extensions:

  * Work as-is
  * Require async-aware versions
* Smaller async-first ecosystem

---

## Testing

| Area                 | FastAPI               | Quart       |
| -------------------- | --------------------- | ----------- |
| Test client          | Excellent (Starlette) | Good        |
| Async tests          | First-class           | First-class |
| Dependency overrides | Built-in              | Manual      |

FastAPI’s dependency injection makes **mocking and testing easier** for APIs.

---

## When to choose which?

### Choose **FastAPI** if:

* You are building:

  * REST APIs
  * Backend-for-frontend
  * Microservices
* You want:

  * Automatic validation
  * OpenAPI docs
  * High performance
* You value:

  * Type safety
  * Clear API contracts

**Typical use cases**

* Mobile / SPA backends
* Public APIs
* Internal microservices

---

### Choose **Quart** if:

* You are:

  * Migrating from Flask
  * Already using Flask patterns/extensions
* You want:

  * Full control
  * Minimal abstraction
* Your app is:

  * More than just an API
  * Template-heavy or custom request handling

**Typical use cases**

* Async web apps
* Flask codebase upgrade
* Custom protocols / streaming

---

## Quick decision guide

> **If this is a new API project → FastAPI**
> **If this is an async Flask migration → Quart**
"""


class FakeChatModel(BaseChatModel):
    def __init__(self, model_id: str, stream_delay_seconds: float = 0.0) -> None:
        super().__init__()
        self._model_id = model_id
        self._stream_delay_seconds = max(stream_delay_seconds, 0.0)
        self._static_response = "This is a fake static response."
        self._random_responses = [_text01, _text02, _text03]

    @property
    def _llm_type(self) -> str:
        return "fake"

    @property
    def _identifying_params(self) -> dict:
        return {"model_id": self._model_id}

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        return self._build_response()

    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        return self._build_response()

    def _stream(
        self, messages, stop=None, run_manager=None, **kwargs
    ) -> Iterator[ChatGenerationChunk]:
        content = self._select_content()
        for chunk in self._iter_chunks(content):
            if run_manager:
                run_manager.on_llm_new_token(chunk)
            if self._stream_delay_seconds > 0:
                time.sleep(self._stream_delay_seconds)
            yield ChatGenerationChunk(message=AIMessageChunk(content=chunk))

    async def _astream(
        self, messages, stop=None, run_manager=None, **kwargs
    ) -> AsyncIterator[ChatGenerationChunk]:
        content = self._select_content()
        for chunk in self._iter_chunks(content):
            if run_manager:
                await run_manager.on_llm_new_token(chunk)
            if self._stream_delay_seconds > 0:
                await asyncio.sleep(self._stream_delay_seconds)
            yield ChatGenerationChunk(message=AIMessageChunk(content=chunk))

    def _select_content(self) -> str:
        if self._model_id == "fake-static":
            return self._static_response
        return random.choice(self._random_responses)

    def _iter_chunks(self, content: str) -> Iterator[str]:
        if self._model_id != "fake-random" or self._stream_delay_seconds <= 0:
            yield content
            return
        chunk_size = 16
        for index in range(0, len(content), chunk_size):
            yield content[index : index + chunk_size]

    def _build_response(self) -> ChatResult:
        content = self._select_content()
        message = AIMessage(content=content)
        return ChatResult(generations=[ChatGeneration(message=message)])
