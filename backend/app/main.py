import logging
import json
import asyncio
import time
import random
import uuid
from datetime import datetime, timezone

# from pathlib import Path

from fastapi import FastAPI, HTTPException, Request

# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


# @app.get("/{full_path:path}")
# async def spa_fallback(full_path: str):
#     index_path = Path("dist") / "index.html"
#     return FileResponse(index_path)


# app.mount(
#     "/assets",
#     StaticFiles(directory="dist/assets"),
#     name="assets",
# )


def sse(payload: dict) -> str:
    """Vercel AI SDK DataStream format"""
    return f"data: {json.dumps(payload, separators=(',', ':'))}\n\n"


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


conversation_store = {
    "conv-quickstart": {
        "id": "conv-quickstart",
        "title": "Project kickoff chat",
        "updatedAt": current_timestamp(),
        "messages": [
            {
                "id": "msg-system",
                "role": "system",
                "parts": [
                    {
                        "type": "text",
                        "text": "You are a helpful project assistant.",
                    }
                ],
            },
            {
                "id": "msg-user-1",
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": "Please outline the next steps for our AI SDK demo.",
                    }
                ],
            },
            {
                "id": "msg-assistant-1",
                "role": "assistant",
                "parts": [
                    {
                        "type": "text",
                        "text": "Sure! I will list the milestones and owners so you can start quickly.",
                    }
                ],
            },
        ],
    },
    "conv-rag": {
        "id": "conv-rag",
        "title": "RAG tuning ideas",
        "updatedAt": current_timestamp(),
        "messages": [
            {
                "id": "msg-user-2",
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": "How can we improve retrieval quality for the docs index?",
                    }
                ],
            },
            {
                "id": "msg-assistant-2",
                "role": "assistant",
                "parts": [
                    {
                        "type": "text",
                        "text": "Consider adding hierarchical chunking and reranking with a cross-encoder.",
                    }
                ],
            },
        ],
    },
}


def parse_user_from_headers(request: Request) -> dict:
    """
    Extract user identity from EasyAuth or IAP headers.
    Falls back to an anonymous principal.
    """
    headers = request.headers

    # Azure App Service EasyAuth
    easy_auth_id = headers.get("x-ms-client-principal-id")
    easy_auth_email = headers.get("x-ms-client-principal-name")
    # TODO: dummy data
    easy_auth_id = "8098fdsgsgrf"
    easy_auth_email = "tanaka.taro@example.com"

    if easy_auth_id:
        return {
            "user_id": easy_auth_id,
            "email": easy_auth_email,
            "provider": "easyauth",
            "first_name": None,
            "last_name": None,
        }

    # Google IAP
    iap_user = headers.get("x-goog-authenticated-user-id")
    iap_email = headers.get("x-goog-authenticated-user-email")
    if iap_user:
        # iap_user format: "accounts.google.com:userid"
        user_id = iap_user.split(":")[-1]
        email = iap_email.split(":")[-1] if iap_email else None
        return {
            "user_id": user_id,
            "email": email,
            "provider": "iap",
            "first_name": None,
            "last_name": None,
        }

    return {
        "user_id": "anonymous",
        "email": None,
        "provider": "unknown",
        "first_name": None,
        "last_name": None,
    }


# Mock NoSQL authz table keyed by user_id.
authz_table = {
    "8098fdsgsgrf": {
        "tools": ["rag01", "rag02"],
        "first_name": "Taro",
        "last_name": "Tanaka",
        "email": "tanaka.taro@example.com",
    },
    "user-rag01": {
        "tools": ["rag01"],
        "first_name": "Jamie",
        "last_name": "Lee",
        "email": "jamie.lee@example.com",
    },
    "user-rag02": {
        "tools": ["rag02"],
        "first_name": "Taylor",
        "last_name": "Kim",
        "email": "taylor.kim@example.com",
    },
}


@app.get("/api/authz")
def get_authorization(request: Request):
    """
    Return access control for the current user.
    In production, this should query a NoSQL/AuthZ store using the user_id.
    """
    user = parse_user_from_headers(request)
    row = authz_table.get(user["user_id"], {})
    tools = row.get("tools", [])

    time.sleep(random.random() * 2)

    return {
        "user": {
            "user_id": user["user_id"],
            "email": row.get("email") or user.get("email"),
            "provider": user.get("provider"),
            "first_name": row.get("first_name") or user.get("first_name"),
            "last_name": row.get("last_name") or user.get("last_name"),
        },
        "tools": tools,
    }


@app.get("/api/conversations")
def conversation_history():
    """Return conversation metadata only."""
    return {
        "conversations": [
            {
                "id": conv["id"],
                "title": conv.get("title") or "Conversation",
                "updatedAt": conv.get("updatedAt") or current_timestamp(),
            }
            for conv in conversation_store.values()
        ]
    }


@app.get("/api/conversations/{conversation_id}")
def conversation_detail(conversation_id: str):
    """Return a single conversation's messages in ai-sdk/useChat format."""
    conversation = conversation_store.get(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "id": conversation["id"],
        "title": conversation.get("title"),
        "updatedAt": conversation.get("updatedAt") or current_timestamp(),
        "messages": conversation.get("messages", []),
    }


@app.post("/api/chat")
def chat(request: Request):
    responses = [
        """
# React Hooks Guide (Detailed)

React Hooks are functions that allow you to use state and lifecycle features
inside function components. They were introduced in **React 16.8** to simplify
component logic and encourage reuse.

## Core Hooks

### useState
The `useState` hook lets you add local state to a function component.

```jsx
const [count, setCount] = useState(0);

return (
  <button onClick={() => setCount(count + 1)}>
    Count: {count}
  </button>
);
```

### useEffect

The `useEffect` hook is used for side effects such as data fetching,
subscriptions, or manually changing the DOM.

```jsx
useEffect(() => {
  document.title = `Count: ${count}`;
  return () => {
    document.title = "React App";
  };
}, [count]);
```

Hooks make it easier to understand how state and effects interact.
""",
        """

## React Hooks Overview

React Hooks let you use React features without writing class components.

### Why Hooks Exist

Before hooks, developers faced several challenges:

* Reusing stateful logic was difficult
* Large class components became hard to maintain
* Lifecycle methods scattered related logic

Hooks solve these problems by letting you group logic by **feature**, not lifecycle.

### Commonly Used Hooks

* **useState** – manage local component state
* **useEffect** – perform side effects
* **useContext** – access context values
* **useRef** – persist values across renders
* **useReducer** – handle complex state transitions

Hooks encourage smaller, more reusable components.
""",
        """

### Why React Hooks Matter

React Hooks fundamentally changed how React applications are built.

## Key Benefits

1. **Cleaner code**
   Function components are easier to read and reason about than class components.

2. **Reusable logic**
   Custom hooks allow you to extract and reuse stateful logic across components.

3. **Better organization**
   Related logic can live together instead of being split across lifecycle methods.

## Rules of Hooks

* Only call hooks at the **top level**
* Only call hooks from **React function components or custom hooks**

By following these rules, React can reliably manage component state and updates.
""",
    ]

    def stream():
        message_id = f"msg-{uuid.uuid4().hex}"
        text_id = "text-1"

        yield sse(
            {
                "type": "start",
                "messageId": message_id,
            }
        )

        yield sse(
            {
                "type": "text-start",
                "id": text_id,
            }
        )

        text = random.choice(responses)
        for token in text.split(" "):
            yield sse(
                {
                    "type": "text-delta",
                    "id": text_id,
                    "delta": token + " ",
                }
            )
            time.sleep(random.uniform(0.0, 0.1))

        yield sse(
            {
                "type": "text-end",
                "id": text_id,
            }
        )

        yield sse(
            {
                "type": "finish",
                "messageMetadata": {
                    "finishReason": "stop",
                },
            }
        )

        yield "data: [DONE]\n\n"

    response = StreamingResponse(
        stream(),
        media_type="text/event-stream",
    )

    response.headers["x-vercel-ai-ui-message-stream"] = "v1"
    response.headers["x-vercel-ai-protocol"] = "data"
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    response.headers["X-Accel-Buffering"] = "no"

    return response

    def stream():
        responses = [
            """
# React Hooks Guide (Detailed)

React Hooks are functions that allow you to use state and lifecycle features
inside function components. They were introduced in **React 16.8** to simplify
component logic and encourage reuse.

## Core Hooks

### useState
The `useState` hook lets you add local state to a function component.

```jsx
const [count, setCount] = useState(0);

return (
  <button onClick={() => setCount(count + 1)}>
    Count: {count}
  </button>
);
```

### useEffect

The `useEffect` hook is used for side effects such as data fetching,
subscriptions, or manually changing the DOM.

```jsx
useEffect(() => {
  document.title = `Count: ${count}`;
  return () => {
    document.title = "React App";
  };
}, [count]);
```

Hooks make it easier to understand how state and effects interact.
""",
            """

## React Hooks Overview

React Hooks let you use React features without writing class components.

### Why Hooks Exist

Before hooks, developers faced several challenges:

* Reusing stateful logic was difficult
* Large class components became hard to maintain
* Lifecycle methods scattered related logic

Hooks solve these problems by letting you group logic by **feature**, not lifecycle.

### Commonly Used Hooks

* **useState** – manage local component state
* **useEffect** – perform side effects
* **useContext** – access context values
* **useRef** – persist values across renders
* **useReducer** – handle complex state transitions

Hooks encourage smaller, more reusable components.
""",
            """

### Why React Hooks Matter

React Hooks fundamentally changed how React applications are built.

## Key Benefits

1. **Cleaner code**
   Function components are easier to read and reason about than class components.

2. **Reusable logic**
   Custom hooks allow you to extract and reuse stateful logic across components.

3. **Better organization**
   Related logic can live together instead of being split across lifecycle methods.

## Rules of Hooks

* Only call hooks at the **top level**
* Only call hooks from **React function components or custom hooks**

By following these rules, React can reliably manage component state and updates.
""",
        ]

        for index, text in enumerate(responses[0]):
            message_id = f"msg-{uuid.uuid4().hex}"
            text_id = f"text-{index + 1}"

            yield sse(
                {
                    "type": "start",
                    "messageId": message_id,
                    "role": "assistant",
                }
            )

            yield sse(
                {
                    "type": "text-start",
                    "id": text_id,
                }
            )

            for token in text.split(" "):
                yield sse(
                    {
                        "type": "text-delta",
                        "id": text_id,
                        "delta": token + " ",
                    }
                )
                time.sleep(random.uniform(0.02, 0.08))

            yield sse(
                {
                    "type": "text-end",
                    "id": text_id,
                }
            )

            yield sse(
                {
                    "type": "finish",
                    "messageId": message_id,
                    "messageMetadata": {
                        "finishReason": "stop",
                    },
                }
            )

        yield "data: [DONE]\n\n"

    response = StreamingResponse(
        stream(),
        media_type="text/event-stream",
    )

    response.headers["x-vercel-ai-ui-message-stream"] = "v1"
    response.headers["x-vercel-ai-protocol"] = "data"
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    response.headers["X-Accel-Buffering"] = "no"

    return response
