from fastapi_ai_sdk.models import AnyStreamEvent, DataEvent, SourceURLEvent

from app.features.retrieval.run.models import (
    ConversationContext,
    QueryContext,
    ResponseContext,
    ToolContext,
)
import app.shared.stream_events as sevents


def build_start_event(message_id: str) -> AnyStreamEvent:
    return sevents.build_start_event(message_id)


def build_text_start_event(text_id: str) -> AnyStreamEvent:
    return sevents.build_text_start_event(text_id)


def build_text_delta_event(text_id: str, delta: str) -> AnyStreamEvent:
    return sevents.build_text_delta_event(text_id, delta)


def build_text_end_event(text_id: str) -> AnyStreamEvent:
    return sevents.build_text_end_event(text_id)


def build_error_event(message: str) -> AnyStreamEvent:
    return sevents.build_error_event(message)


def build_conversation_event(
    conversation_ctx: ConversationContext,
    tool_ctx: ToolContext,
) -> AnyStreamEvent:
    return DataEvent.create(
        "conversation",
        {
            "convId": conversation_ctx.conversation_id,
            "toolId": tool_ctx.tool_id_for_conversation,
        },
    )


def build_cot_reset_event() -> AnyStreamEvent:
    return DataEvent.create(
        "cot",
        {
            "reset": True,
            "open": True,
            "steps": [
                {"id": "query", "label": "Query", "status": "complete"},
                {"id": "search", "label": "Search", "status": "pending"},
                {"id": "answer", "label": "Answer", "status": "pending"},
            ],
        },
    )


def build_cot_query_complete_event(query_ctx: QueryContext) -> AnyStreamEvent:
    return DataEvent.create(
        "cot",
        {
            "step": {
                "id": "query",
                "status": "complete",
                "description": f"Query: {query_ctx.user_query}",
            }
        },
    )


def build_cot_search_active_event() -> AnyStreamEvent:
    return DataEvent.create(
        "cot",
        {
            "step": {
                "id": "search",
                "status": "active",
                "description": "Searching documents...",
            }
        },
    )


def build_model_event(message_id: str, model_id: str | None) -> AnyStreamEvent | None:
    if not model_id:
        return None
    return DataEvent.create(
        "model",
        {
            "messageId": message_id,
            "modelId": model_id,
        },
    )


def build_rag_event(response_ctx: ResponseContext) -> AnyStreamEvent:
    return DataEvent.create("rag", response_ctx.retrieval_response.model_dump(by_alias=True))


def build_sources_event(response_ctx: ResponseContext) -> AnyStreamEvent:
    return DataEvent.create(
        "sources",
        {"reset": True, "sources": response_ctx.sources_payload},
    )


def build_source_url_events(response_ctx: ResponseContext) -> list[SourceURLEvent]:
    return [
        SourceURLEvent(sourceId=source["id"], url=source["url"])
        for source in response_ctx.sources_payload
    ]


def build_cot_search_complete_event(
    result_count: int,
    result_titles: list[str],
) -> AnyStreamEvent:
    return DataEvent.create(
        "cot",
        {
            "step": {
                "id": "search",
                "status": "complete",
                "description": f"Retrieved {result_count} results.",
                "resultCount": result_count,
                "resultTitles": result_titles,
            }
        },
    )


def build_title_event(title: str) -> AnyStreamEvent:
    return DataEvent.create("title", {"title": title})


def build_cot_answer_active_event() -> AnyStreamEvent:
    return DataEvent.create(
        "cot",
        {
            "step": {
                "id": "answer",
                "status": "active",
                "description": "Generating answer...",
            }
        },
    )


def build_cot_answer_complete_event() -> AnyStreamEvent:
    return DataEvent.create(
        "cot",
        {
            "step": {
                "id": "answer",
                "status": "complete",
                "description": "Answer generated successfully.",
            }
        },
    )
