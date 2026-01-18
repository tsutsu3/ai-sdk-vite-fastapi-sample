from collections.abc import AsyncIterator

from fastapi_ai_sdk.models import AnyStreamEvent
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, ConfigDict, Field

from app.ai.history.factory import build_session_id
from app.ai.models import HistoryKey
from app.features.retrieval.run import event_builder
from app.features.retrieval.run.execution_service import RetrievalExecutionService
from app.features.retrieval.run.longform_graph import (
    LongformGraphState,
    build_longform_graph,
    build_longform_state,
)
from app.features.retrieval.run.models import (
    AuthContext,
    ConversationContext,
    QueryContext,
    ResponseContext,
    RetrievalContext,
    ToolContext,
)
from app.features.retrieval.run.persistence_service import RetrievalPersistenceService
from app.features.retrieval.run.utils import extract_last_user_message
from app.features.retrieval.schemas import RetrievalQueryRequest


class LongformPipelineState(BaseModel):
    """State shared across the longform RAG pipeline graph."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    payload: RetrievalQueryRequest
    auth_ctx: AuthContext
    tool_ctx: ToolContext
    conversation_ctx: ConversationContext
    message_repo: object
    message_id: str
    text_id: str
    query_ctx: QueryContext | None = None
    retrieval_ctx: RetrievalContext | None = None
    response_ctx: ResponseContext | None = None
    longform_state: LongformGraphState | None = None
    events: list[AnyStreamEvent] = Field(default_factory=list)
    answer_stream: AsyncIterator[AnyStreamEvent] | None = None


def _coerce_state(state) -> LongformPipelineState:
    if isinstance(state, LongformPipelineState):
        return state
    return LongformPipelineState.model_validate(state)


def build_longform_pipeline_graph(
    *,
    execution: RetrievalExecutionService,
    persistence: RetrievalPersistenceService,
    chapter_concurrency: int,
):
    """Build the longform RAG pipeline graph (planning -> longform -> proofread)."""
    steps_graph = build_longform_graph(
        execution=execution,
        chapter_concurrency=chapter_concurrency,
    )

    async def _plan_query(state):
        parsed = _coerce_state(state)
        payload = parsed.payload
        tool = parsed.tool_ctx.tool
        mode = payload.mode or (tool.mode if tool else "simple")
        user_query = payload.query.strip()
        last_user = extract_last_user_message(payload.messages)
        if last_user:
            user_query = last_user
        search_query = user_query
        if payload.hyde_enabled and mode != "answer":
            hyde_query = await execution.generate_hypothetical_answer(
                messages=payload.messages,
                query=user_query,
                hyde_prompt=tool.hyde_prompt if tool else None,
            )
            if hyde_query:
                search_query = hyde_query
        elif mode == "chat" and tool and tool.query_prompt:
            generated = await execution.generate_search_query(
                prompt=tool.query_prompt,
                messages=payload.messages,
                query=user_query,
            )
            if generated and generated != "0":
                search_query = generated
        return {
            "query_ctx": QueryContext(
                mode=mode,
                user_query=user_query,
                search_query=search_query,
                last_user_message=last_user,
            )
        }

    async def _emit_search_start(state):
        parsed = _coerce_state(state)
        if parsed.query_ctx is None:
            raise RuntimeError("query_ctx is missing")
        events = list(parsed.events)
        events.extend(
            [
                event_builder.build_start_event(parsed.message_id),
                event_builder.build_conversation_event(
                    parsed.conversation_ctx,
                    parsed.tool_ctx,
                ),
                event_builder.build_cot_reset_event(),
                event_builder.build_cot_query_complete_event(parsed.query_ctx),
                event_builder.build_cot_search_active_event(),
            ]
        )
        return {"events": events}

    async def _retrieve(state):
        parsed = _coerce_state(state)
        query_ctx = parsed.query_ctx
        if query_ctx is None:
            raise RuntimeError("query_ctx is missing")
        retrieval_ctx = await execution.retrieve_results(
            payload=parsed.payload,
            tool_ctx=parsed.tool_ctx,
            query_ctx=query_ctx,
        )
        return {"retrieval_ctx": retrieval_ctx}

    async def _build_response(state):
        parsed = _coerce_state(state)
        if parsed.retrieval_ctx is None:
            raise RuntimeError("retrieval_ctx is missing")
        if parsed.query_ctx is None:
            raise RuntimeError("query_ctx is missing")
        response_ctx = execution.build_response_context(
            payload=parsed.payload,
            tool_ctx=parsed.tool_ctx,
            query_ctx=parsed.query_ctx,
            results=parsed.retrieval_ctx.results,
            message_id=parsed.message_id,
            text_id=parsed.text_id,
        )
        return {"response_ctx": response_ctx}

    async def _emit_search_results(state):
        parsed = _coerce_state(state)
        retrieval_ctx = parsed.retrieval_ctx
        response_ctx = parsed.response_ctx
        if retrieval_ctx is None or response_ctx is None:
            raise RuntimeError("retrieval_ctx/response_ctx are missing")
        events = list(parsed.events)
        model_event = event_builder.build_model_event(
            parsed.message_id,
            response_ctx.selected_model,
        )
        if model_event:
            events.append(model_event)
        events.append(event_builder.build_rag_event(response_ctx))
        events.append(event_builder.build_sources_event(response_ctx))
        events.extend(event_builder.build_source_url_events(response_ctx))
        events.append(
            event_builder.build_cot_search_complete_event(
                result_count=len(retrieval_ctx.results),
                result_titles=response_ctx.result_titles,
            )
        )
        return {"events": events}

    async def _maybe_title(state):
        parsed = _coerce_state(state)
        response_ctx = parsed.response_ctx
        if response_ctx is None:
            raise RuntimeError("response_ctx is missing")
        generated_title = await persistence.maybe_generate_title(
            auth_ctx=parsed.auth_ctx,
            tool_ctx=parsed.tool_ctx,
            conversation_ctx=parsed.conversation_ctx,
            response_ctx=response_ctx,
        )
        events = list(parsed.events)
        if generated_title:
            events.append(event_builder.build_title_event(generated_title))
        return {"events": events}

    async def _run_longform_steps(state):
        parsed = _coerce_state(state)
        if parsed.query_ctx is None:
            raise RuntimeError("query_ctx is missing")
        if parsed.retrieval_ctx is None:
            raise RuntimeError("retrieval_ctx is missing")
        model_id = parsed.response_ctx.selected_model if parsed.response_ctx else None
        longform_state = build_longform_state(
            payload=parsed.payload,
            tool_ctx=parsed.tool_ctx,
            query_ctx=parsed.query_ctx,
            results=parsed.retrieval_ctx.results,
            model_id=model_id,
        )
        state_dict = await steps_graph.ainvoke(longform_state.model_dump(mode="python"))
        return {"longform_state": LongformGraphState.model_validate(state_dict)}

    async def _build_answer_stream(state):
        parsed = _coerce_state(state)
        if parsed.response_ctx is None:
            raise RuntimeError("response_ctx is missing")
        if parsed.longform_state is None:
            raise RuntimeError("longform_state is missing")

        proofread_prompt = parsed.payload.proofread_prompt or (
            parsed.tool_ctx.tool.proofread_prompt if parsed.tool_ctx.tool else None
        )

        async def _answer_stream() -> AsyncIterator[AnyStreamEvent]:
            yield event_builder.build_cot_answer_active_event()
            yield event_builder.build_text_start_event(parsed.text_id)
            session_id = build_session_id(
                HistoryKey(
                    tenant_id=parsed.auth_ctx.tenant_id,
                    user_id=parsed.auth_ctx.user_id,
                    conversation_id=parsed.conversation_ctx.conversation_id,
                )
            )
            async for delta in execution.stream_proofread(
                prompt=proofread_prompt,
                draft_text=parsed.longform_state.merged_text,
                session_id=session_id,
                message_repo=parsed.message_repo,
                model_id=parsed.response_ctx.selected_model,
                follow_up_questions_prompt=(
                    parsed.tool_ctx.tool.follow_up_questions_prompt
                    if parsed.tool_ctx.tool
                    else ""
                ),
                injected_prompt=parsed.payload.injected_prompt,
            ):
                yield event_builder.build_text_delta_event(parsed.text_id, delta)
            yield event_builder.build_text_end_event(parsed.text_id)
            yield event_builder.build_cot_answer_complete_event()

        return {"answer_stream": _answer_stream()}

    graph = StateGraph(LongformPipelineState)
    graph.add_node("plan_query", _plan_query)
    graph.add_node("emit_search_start", _emit_search_start)
    graph.add_node("retrieve", _retrieve)
    graph.add_node("response", _build_response)
    graph.add_node("emit_search_results", _emit_search_results)
    graph.add_node("title", _maybe_title)
    graph.add_node("longform_steps", _run_longform_steps)
    graph.add_node("answer", _build_answer_stream)
    graph.set_entry_point("plan_query")
    graph.add_edge("plan_query", "emit_search_start")
    graph.add_edge("emit_search_start", "retrieve")
    graph.add_edge("retrieve", "response")
    graph.add_edge("response", "emit_search_results")
    graph.add_edge("emit_search_results", "title")
    graph.add_edge("title", "longform_steps")
    graph.add_edge("longform_steps", "answer")
    graph.add_edge("answer", END)
    return graph.compile()


def build_longform_pipeline_state(
    *,
    payload: RetrievalQueryRequest,
    auth_ctx: AuthContext,
    tool_ctx: ToolContext,
    conversation_ctx: ConversationContext,
    message_repo: object,
    message_id: str,
    text_id: str,
) -> LongformPipelineState:
    """Initialize the longform pipeline state."""
    return LongformPipelineState(
        payload=payload,
        auth_ctx=auth_ctx,
        tool_ctx=tool_ctx,
        conversation_ctx=conversation_ctx,
        message_repo=message_repo,
        message_id=message_id,
        text_id=text_id,
    )
