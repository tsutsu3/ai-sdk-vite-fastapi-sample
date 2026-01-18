import uuid
from collections.abc import AsyncIterator
from logging import getLogger
from typing import Any

from fastapi_ai_sdk.models import (
    AnyStreamEvent,
    ReasoningDeltaEvent,
    ReasoningEndEvent,
    ReasoningStartEvent,
)
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, ConfigDict, Field

from app.features.chat.run.chat_execution_service import ChatExecutionService
from app.features.chat.run.errors import RunServiceError
from app.features.chat.run.models import StreamContext

logger = getLogger(__name__)


class ChatGraphState(BaseModel):
    """State shared across the chat execution graph."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    context: StreamContext
    events: list[AnyStreamEvent] = Field(default_factory=list)
    usage_payload: list[dict[str, Any]] = Field(default_factory=list)
    delta_stream: AsyncIterator[str] | None = None


def _coerce_state(state) -> ChatGraphState:
    if isinstance(state, ChatGraphState):
        return state
    return ChatGraphState.model_validate(state)


def build_chat_graph(*, execution: ChatExecutionService):
    """Build the chat execution graph (branch -> stream)."""

    def _route(state) -> str:
        parsed = _coerce_state(state)
        return "tool" if parsed.context.tool_id else "chat"

    async def _chat_stream(state):
        parsed = _coerce_state(state)
        user_text = execution.extract_user_text(parsed.context.messages)
        if not user_text:
            raise RunServiceError("Missing user input.")
        usage_payload = execution.build_chat_request_payload(user_text)
        delta_stream = execution.stream_chat(
            context=parsed.context,
            user_text=user_text,
        )
        return {
            "usage_payload": usage_payload,
            "delta_stream": delta_stream,
        }

    async def _tool_stream(state):
        parsed = _coerce_state(state)
        events = list(parsed.events)
        retrieval_context = await execution.build_retrieval_context(parsed.context)
        reasoning_id = f"reasoning_{uuid.uuid4()}"
        events.append(ReasoningStartEvent(id=reasoning_id))
        events.append(
            ReasoningDeltaEvent(
                id=reasoning_id,
                delta=f"Retrieval tool: {parsed.context.tool_id}\n",
            )
        )
        if retrieval_context:
            logger.debug(
                "run.retrieval.context tool_id=%s results=%s",
                parsed.context.tool_id,
                len(retrieval_context.results),
            )
            query_preview = retrieval_context.query
            if len(query_preview) > 120:
                query_preview = query_preview[:117].rstrip() + "..."
            events.append(
                ReasoningDeltaEvent(
                    id=reasoning_id,
                    delta=f"Query: {query_preview}\n",
                )
            )
            events.append(
                ReasoningDeltaEvent(
                    id=reasoning_id,
                    delta=(f"Retrieved {len(retrieval_context.results)} results.\n"),
                )
            )
        else:
            events.append(
                ReasoningDeltaEvent(
                    id=reasoning_id,
                    delta="No retrieval context was added.\n",
                )
            )
        events.append(ReasoningEndEvent(id=reasoning_id))

        user_text = execution.extract_user_text(parsed.context.messages)
        if not user_text:
            raise RunServiceError("Missing user input.")

        plan = execution.build_tool_execution_plan(
            parsed.context,
            retrieval_context,
        )
        delta_stream = execution.stream_tool(
            context=parsed.context,
            user_text=user_text,
            system_prompt=plan.system_prompt,
        )
        return {
            "events": events,
            "usage_payload": plan.request_payload,
            "delta_stream": delta_stream,
        }

    graph = StateGraph(ChatGraphState)
    graph.add_node("route", lambda state: {})
    graph.add_node("chat", _chat_stream)
    graph.add_node("tool", _tool_stream)
    graph.set_entry_point("route")
    graph.add_conditional_edges("route", _route, {"chat": "chat", "tool": "tool"})
    graph.add_edge("chat", END)
    graph.add_edge("tool", END)
    return graph.compile()


def build_chat_state(*, context: StreamContext) -> ChatGraphState:
    """Initialize the chat graph state."""
    return ChatGraphState(context=context)
