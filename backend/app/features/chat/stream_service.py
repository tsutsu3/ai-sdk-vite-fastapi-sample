import json
import random
import time
import uuid
from collections.abc import Iterator


def sse(payload: dict[str, object]) -> str:
    """Vercel AI SDK DataStream format."""
    return f"data: {json.dumps(payload, separators=(',', ':'))}\n\n"


class ChatStreamService:
    def __init__(self) -> None:
        self._responses = [
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

    def stream(self) -> Iterator[str]:
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

        text = random.choice(self._responses)
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
