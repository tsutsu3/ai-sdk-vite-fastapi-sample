from langgraph.graph import END, StateGraph
from pydantic import BaseModel, ConfigDict, Field

from app.features.retrieval.run.execution_service import RetrievalExecutionService
from app.features.retrieval.run.models import QueryContext, ResponseContext, ToolContext
from app.features.retrieval.schemas import RetrievalQueryRequest


class RetrievalGraphState(BaseModel):
    """State shared across the default RAG graph nodes."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    payload: RetrievalQueryRequest
    tool_ctx: ToolContext
    query_ctx: QueryContext
    message_id: str
    text_id: str
    retrieval_ctx: object | None = Field(default=None)
    response_ctx: ResponseContext | None = Field(default=None)


def _coerce_state(state) -> RetrievalGraphState:
    if isinstance(state, RetrievalGraphState):
        return state
    return RetrievalGraphState.model_validate(state)


def build_retrieval_graph(
    *,
    execution: RetrievalExecutionService,
):
    """Build the default RAG graph (retrieve -> build response context)."""

    async def _retrieve(state):
        parsed = _coerce_state(state)
        retrieval_ctx = await execution.retrieve_results(
            payload=parsed.payload,
            tool_ctx=parsed.tool_ctx,
            query_ctx=parsed.query_ctx,
        )
        return {"retrieval_ctx": retrieval_ctx}

    async def _build_response(state):
        parsed = _coerce_state(state)
        retrieval_ctx = parsed.retrieval_ctx
        if retrieval_ctx is None:
            raise RuntimeError("retrieval_ctx is missing")
        response_ctx = execution.build_response_context(
            payload=parsed.payload,
            tool_ctx=parsed.tool_ctx,
            query_ctx=parsed.query_ctx,
            results=retrieval_ctx.results,
            message_id=parsed.message_id,
            text_id=parsed.text_id,
        )
        return {"response_ctx": response_ctx}

    graph = StateGraph(RetrievalGraphState)
    graph.add_node("retrieve", _retrieve)
    graph.add_node("response", _build_response)
    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "response")
    graph.add_edge("response", END)
    return graph.compile()


def build_retrieval_state(
    *,
    payload: RetrievalQueryRequest,
    tool_ctx: ToolContext,
    query_ctx: QueryContext,
    message_id: str,
    text_id: str,
) -> RetrievalGraphState:
    """Initialize retrieval graph state for the default RAG flow."""
    return RetrievalGraphState(
        payload=payload,
        tool_ctx=tool_ctx,
        query_ctx=query_ctx,
        message_id=message_id,
        text_id=text_id,
    )
