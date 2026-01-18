import logging
from collections.abc import AsyncIterator

from fastapi_ai_sdk.models import AnyStreamEvent

from app.ai.history.factory import build_session_id
from app.ai.models import HistoryKey
from app.features.retrieval.run import event_builder
from app.features.retrieval.run.execution_service import RetrievalExecutionService
from app.features.retrieval.run.models import (
    AuthContext,
    ConversationContext,
    QueryContext,
    ToolContext,
)
from app.features.retrieval.run.persistence_service import RetrievalPersistenceService
from app.features.retrieval.run.utils import format_sources, truncate_text, uuid4_str
from app.features.retrieval.schemas import RetrievalQueryRequest

logger = logging.getLogger(__name__)


class RetrievalStreamCoordinator:
    """Control event ordering and stream flow for RAG responses."""

    def __init__(
        self,
        *,
        execution: RetrievalExecutionService,
        persistence: RetrievalPersistenceService,
    ) -> None:
        self._execution = execution
        self._persistence = persistence

    async def stream(
        self,
        *,
        payload: RetrievalQueryRequest,
        auth_ctx: AuthContext,
        tool_ctx: ToolContext,
        query_ctx: QueryContext,
        conversation_ctx: ConversationContext,
        message_repo,
    ) -> AsyncIterator[AnyStreamEvent]:
        if payload.pipeline == "longform":
            async for event in self._stream_longform(
                payload=payload,
                auth_ctx=auth_ctx,
                tool_ctx=tool_ctx,
                query_ctx=query_ctx,
                conversation_ctx=conversation_ctx,
                message_repo=message_repo,
            ):
                yield event
        else:
            async for event in self._stream_default(
                payload=payload,
                auth_ctx=auth_ctx,
                tool_ctx=tool_ctx,
                query_ctx=query_ctx,
                conversation_ctx=conversation_ctx,
                message_repo=message_repo,
            ):
                yield event

    async def _stream_default(
        self,
        *,
        payload: RetrievalQueryRequest,
        auth_ctx: AuthContext,
        tool_ctx: ToolContext,
        query_ctx: QueryContext,
        conversation_ctx: ConversationContext,
        message_repo,
    ) -> AsyncIterator[AnyStreamEvent]:
        response_text = ""
        message_id = f"msg-{uuid4_str()}"
        text_id = "text-1"

        yield event_builder.build_start_event(message_id)
        yield event_builder.build_conversation_event(conversation_ctx, tool_ctx)
        yield event_builder.build_cot_reset_event()
        yield event_builder.build_cot_query_complete_event(query_ctx)
        yield event_builder.build_cot_search_active_event()

        retrieval_ctx = await self._execution.retrieve_results(
            payload=payload,
            tool_ctx=tool_ctx,
            query_ctx=query_ctx,
        )
        response_ctx = self._execution.build_response_context(
            payload=payload,
            tool_ctx=tool_ctx,
            query_ctx=query_ctx,
            results=retrieval_ctx.results,
            message_id=message_id,
            text_id=text_id,
        )

        model_event = event_builder.build_model_event(message_id, response_ctx.selected_model)
        if model_event:
            yield model_event
        yield event_builder.build_rag_event(response_ctx)
        yield event_builder.build_sources_event(response_ctx)
        for source_event in event_builder.build_source_url_events(response_ctx):
            yield source_event
        yield event_builder.build_cot_search_complete_event(
            result_count=len(retrieval_ctx.results),
            result_titles=response_ctx.result_titles,
        )

        generated_title = await self._persistence.maybe_generate_title(
            auth_ctx=auth_ctx,
            tool_ctx=tool_ctx,
            conversation_ctx=conversation_ctx,
            response_ctx=response_ctx,
        )
        if generated_title:
            yield event_builder.build_title_event(generated_title)

        yield event_builder.build_cot_answer_active_event()
        yield event_builder.build_text_start_event(text_id)

        if query_ctx.mode == "answer" and retrieval_ctx.documents:
            answer_doc = next(
                (doc for doc in retrieval_ctx.documents if doc.metadata.get("type") == "answer"),
                None,
            )
            if answer_doc:
                response_text = answer_doc.page_content
                yield event_builder.build_text_delta_event(text_id, response_text)
            else:
                response_text = "No answer generated."
                yield event_builder.build_text_delta_event(text_id, response_text)
        else:
            session_id = build_session_id(
                HistoryKey(
                    tenant_id=auth_ctx.tenant_id,
                    user_id=auth_ctx.user_id,
                    conversation_id=conversation_ctx.conversation_id,
                )
            )
            async for delta in self._execution.stream_answer(
                documents=retrieval_ctx.documents,
                system_prompt=response_ctx.system_prompt,
                question=response_ctx.question,
                session_id=session_id,
                message_repo=message_repo,
                follow_up_questions_prompt=(
                    tool_ctx.tool.follow_up_questions_prompt if tool_ctx.tool else ""
                ),
                injected_prompt=payload.injected_prompt,
            ):
                yield event_builder.build_text_delta_event(text_id, delta)
                response_text += delta

        yield event_builder.build_text_end_event(text_id)
        logger.debug(
            "rag.query.response_raw provider=%s data_source=%s message_id=%s text=%s",
            tool_ctx.provider_id,
            tool_ctx.data_source,
            message_id,
            truncate_text(response_text, 160),
        )
        yield event_builder.build_cot_answer_complete_event()

        await self._persistence.save_messages(
            auth_ctx=auth_ctx,
            conversation_ctx=conversation_ctx,
            response_ctx=response_ctx,
            response_text=response_text,
        )
        await self._persistence.record_usage(
            auth_ctx=auth_ctx,
            conversation_ctx=conversation_ctx,
            response_ctx=response_ctx,
            response_text=response_text,
        )

    async def _stream_longform(
        self,
        *,
        payload: RetrievalQueryRequest,
        auth_ctx: AuthContext,
        tool_ctx: ToolContext,
        query_ctx: QueryContext,
        conversation_ctx: ConversationContext,
        message_repo,
    ) -> AsyncIterator[AnyStreamEvent]:
        response_text = ""
        message_id = f"msg-{uuid4_str()}"
        text_id = "text-1"

        yield event_builder.build_start_event(message_id)
        yield event_builder.build_conversation_event(conversation_ctx, tool_ctx)
        yield event_builder.build_cot_reset_event()
        yield event_builder.build_cot_query_complete_event(query_ctx)
        yield event_builder.build_cot_search_active_event()

        retrieval_ctx = await self._execution.retrieve_results(
            payload=payload,
            tool_ctx=tool_ctx,
            query_ctx=query_ctx,
        )
        response_ctx = self._execution.build_response_context(
            payload=payload,
            tool_ctx=tool_ctx,
            query_ctx=query_ctx,
            results=retrieval_ctx.results,
            message_id=message_id,
            text_id=text_id,
        )

        model_event = event_builder.build_model_event(message_id, response_ctx.selected_model)
        if model_event:
            yield model_event
        yield event_builder.build_rag_event(response_ctx)
        yield event_builder.build_sources_event(response_ctx)
        for source_event in event_builder.build_source_url_events(response_ctx):
            yield source_event
        yield event_builder.build_cot_search_complete_event(
            result_count=len(retrieval_ctx.results),
            result_titles=response_ctx.result_titles,
        )

        generated_title = await self._persistence.maybe_generate_title(
            auth_ctx=auth_ctx,
            tool_ctx=tool_ctx,
            conversation_ctx=conversation_ctx,
            response_ctx=response_ctx,
        )
        if generated_title:
            yield event_builder.build_title_event(generated_title)

        yield event_builder.build_cot_answer_active_event()
        yield event_builder.build_text_start_event(text_id)

        chapter_count = max(1, min(payload.chapter_count, 12))
        sources_text = format_sources(retrieval_ctx.results, 1000)
        user_query = query_ctx.last_user_message or query_ctx.user_query
        model_id = response_ctx.selected_model
        template_prompt = payload.template_prompt or (
            tool_ctx.tool.template_prompt if tool_ctx.tool else None
        )
        chapter_prompt = payload.chapter_prompt or (
            tool_ctx.tool.chapter_prompt if tool_ctx.tool else None
        )
        merge_prompt = payload.merge_prompt or (
            tool_ctx.tool.merge_prompt if tool_ctx.tool else None
        )
        proofread_prompt = payload.proofread_prompt or (
            tool_ctx.tool.proofread_prompt if tool_ctx.tool else None
        )

        template_text, template_payload = await self._execution.generate_template(
            prompt=template_prompt,
            messages=payload.messages,
            query=user_query,
            sources=sources_text,
            chapter_count=chapter_count,
            model_id=model_id,
            injected_prompt=payload.injected_prompt,
        )
        await self._persistence.record_usage_entry(
            auth_ctx=auth_ctx,
            conversation_ctx=conversation_ctx,
            message_id=f"msg-{uuid4_str()}",
            model_id=model_id,
            request_payload=template_payload,
            response_text=template_text,
        )

        chapter_titles = self._resolve_chapter_titles(
            payload.chapter_titles,
            template_text,
            chapter_count,
        )
        chapters: list[str] = []
        for index, title in enumerate(chapter_titles, start=1):
            chapter_text, chapter_payload = (
                await self._execution.generate_chapter(
                    prompt=chapter_prompt,
                    messages=payload.messages,
                    query=user_query,
                    sources=sources_text,
                    template_text=template_text,
                    chapter_title=title,
                    chapter_index=index,
                    chapter_count=len(chapter_titles),
                    model_id=model_id,
                    injected_prompt=payload.injected_prompt,
                )
            )
            chapters.append(f"{title}\n{chapter_text}".strip())
            await self._persistence.record_usage_entry(
                auth_ctx=auth_ctx,
                conversation_ctx=conversation_ctx,
                message_id=f"msg-{uuid4_str()}",
                model_id=model_id,
                request_payload=chapter_payload,
                response_text=chapter_text,
            )

        merged_text, merge_payload = await self._execution.merge_sections(
            prompt=merge_prompt,
            messages=payload.messages,
            sources=sources_text,
            section_text="\n\n".join(chapters),
            model_id=model_id,
            injected_prompt=payload.injected_prompt,
        )
        await self._persistence.record_usage_entry(
            auth_ctx=auth_ctx,
            conversation_ctx=conversation_ctx,
            message_id=f"msg-{uuid4_str()}",
            model_id=model_id,
            request_payload=merge_payload,
            response_text=merged_text,
        )

        session_id = build_session_id(
            HistoryKey(
                tenant_id=auth_ctx.tenant_id,
                user_id=auth_ctx.user_id,
                conversation_id=conversation_ctx.conversation_id,
            )
        )
        async for delta in self._execution.stream_proofread(
            prompt=proofread_prompt,
            draft_text=merged_text,
            session_id=session_id,
            message_repo=message_repo,
            model_id=model_id,
            follow_up_questions_prompt=(
                tool_ctx.tool.follow_up_questions_prompt if tool_ctx.tool else ""
            ),
            injected_prompt=payload.injected_prompt,
        ):
            yield event_builder.build_text_delta_event(text_id, delta)
            response_text += delta

        await self._persistence.record_usage_entry(
            auth_ctx=auth_ctx,
            conversation_ctx=conversation_ctx,
            message_id=message_id,
            model_id=model_id,
            request_payload=None,
            response_text=response_text,
        )

        yield event_builder.build_text_end_event(text_id)
        logger.debug(
            "rag.longform.response_raw provider=%s data_source=%s message_id=%s text=%s",
            tool_ctx.provider_id,
            tool_ctx.data_source,
            message_id,
            truncate_text(response_text, 160),
        )
        yield event_builder.build_cot_answer_complete_event()

        await self._persistence.save_messages(
            auth_ctx=auth_ctx,
            conversation_ctx=conversation_ctx,
            response_ctx=response_ctx,
            response_text=response_text,
        )

    @staticmethod
    def _resolve_chapter_titles(
        raw_titles: list[str],
        template_text: str,
        chapter_count: int,
    ) -> list[str]:
        titles = [title.strip() for title in raw_titles if title.strip()]
        if not titles and template_text:
            for line in template_text.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                cleaned = stripped.lstrip("-*0123456789. )\t").strip()
                if not cleaned:
                    continue
                titles.append(cleaned)
                if len(titles) >= chapter_count:
                    break
        if not titles:
            titles = [f"Section {index}" for index in range(1, chapter_count + 1)]
        return titles[:chapter_count]
