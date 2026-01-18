import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import (
    RunnableLambda,
    RunnableParallel,
    RunnableWithMessageHistory,
)

from app.ai.history.factory import build_history_factory
from app.ai.models import MemoryPolicy, RetrievalPolicy
from app.ai.ports import ChatModelBuilder, ChatModelResolver, RetrieverBuilder
from app.core.config import AppConfig, ChatCapabilities
from app.features.retrieval.langchain_adapters import documents_to_results
from app.features.retrieval.run.models import (
    QueryContext,
    ResponseContext,
    RetrievalContext,
    ToolContext,
)
from app.features.retrieval.run.utils import (
    build_answer_payload,
    build_prompt_payload,
    extract_delta,
    format_sources,
    preview_payload,
    resolve_embedding_model,
    resolve_index_name,
    resolve_result_titles,
    resolve_search_method,
    resolve_zero_reason,
)
from app.features.retrieval.schemas import (
    RetrievalMessage,
    RetrievalQueryRequest,
    RetrievalQueryResponse,
)
from app.shared.langchain_utils import to_langchain_messages_from_roles
from app.shared.llm_resolver import resolve_chat_model_spec

logger = logging.getLogger(__name__)

_DEFAULT_HYDE_PROMPT = (
    "Write a short hypothetical answer to the user's question to improve retrieval. "
    "Use the same language as the question. Do not mention sources. Keep it concise."
)
_DEFAULT_TEMPLATE_PROMPT = (
    "Create a concise document template with section titles and short goals. "
    "Use the provided sources for grounding."
)
_DEFAULT_CHAPTER_PROMPT = (
    "Write the requested section using the template and sources. "
    "Keep the tone consistent and avoid unsupported claims."
)
_DEFAULT_MERGE_PROMPT = (
    "Merge the sections into a single cohesive document. "
    "Preserve headings and remove redundancy."
)
_DEFAULT_PROOFREAD_PROMPT = (
    "Proofread and polish the draft while preserving meaning and structure."
)


class RetrievalExecutionService:
    """Run retrieval and answer generation without persistence or event concerns."""

    def __init__(
        self,
        *,
        app_config: AppConfig,
        chat_caps: ChatCapabilities,
        resolver: ChatModelResolver,
        builder: ChatModelBuilder,
        retriever_builder: RetrieverBuilder,
        memory_policy: MemoryPolicy,
    ) -> None:
        self._app_config = app_config
        self._chat_caps = chat_caps
        self._resolver = resolver
        self._builder = builder
        self._retriever_builder = retriever_builder
        self._memory_policy = memory_policy

    async def generate_search_query(
        self,
        *,
        prompt: str,
        messages: list[RetrievalMessage],
        query: str,
    ) -> str:
        model_spec = self._resolve_model_spec(None)
        llm = self._builder(self._app_config, model_spec, streaming=False)
        llm = llm.bind(temperature=0.0)

        history = to_langchain_messages_from_roles(messages)
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", "{query_prompt}"),
                MessagesPlaceholder("history"),
                ("human", "{query}"),
            ]
        )
        chain = prompt_template | llm
        response = await chain.ainvoke(
            {"query_prompt": prompt, "history": history, "query": query},
        )

        logger.debug(
            "rag.query.generated_query model=%s prompt=%s query=%s response=%s",
            model_spec.model_id,
            prompt,
            query,
            response.content,
        )

        return (response.content or "").strip()

    async def generate_hypothetical_answer(
        self,
        *,
        messages: list[RetrievalMessage],
        query: str,
        hyde_prompt: str | None = None,
    ) -> str:
        system_prompt = (hyde_prompt or "").strip() or _DEFAULT_HYDE_PROMPT
        model_spec = self._resolve_model_spec(None)
        llm = self._builder(self._app_config, model_spec, streaming=False)
        llm = llm.bind(temperature=0.0)

        history = to_langchain_messages_from_roles(messages)
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", "{hyde_prompt}"),
                MessagesPlaceholder("history"),
                ("human", "{query}"),
            ]
        )
        chain = prompt_template | llm
        response = await chain.ainvoke(
            {"hyde_prompt": system_prompt, "history": history, "query": query},
        )

        logger.debug(
            "rag.query.hypothetical_answer model=%s prompt=%s query=%s response=%s",
            model_spec.model_id,
            system_prompt,
            query,
            response.content,
        )

        return (response.content or "").strip()

    def resolve_model_id(self, model_id: str | None) -> str | None:
        """Resolve the model id used for longform steps."""
        model_spec = self._resolve_model_spec(model_id)
        return model_spec.model_id if model_spec else None

    async def generate_template(
        self,
        *,
        prompt: str | None,
        messages: list[RetrievalMessage],
        query: str,
        sources: str,
        chapter_count: int,
        model_id: str | None,
        injected_prompt: str | None = None,
    ) -> tuple[str, list[dict[str, str]]]:
        system_prompt = self._compose_system_prompt(
            (prompt or "").strip() or _DEFAULT_TEMPLATE_PROMPT,
            injected_prompt,
            None,
        )
        user_text = (
            "User request:\n"
            f"{query}\n\n"
            f"Desired chapter count: {chapter_count}\n\n"
            f"Sources:\n{sources}"
        )
        request_payload = build_prompt_payload(
            system_prompt=system_prompt,
            messages=messages,
            user_text=user_text,
        )
        response_text = await self._invoke_prompt(
            system_prompt=system_prompt,
            messages=messages,
            user_text=user_text,
            model_id=model_id,
        )
        logger.debug(
            "rag.longform.template prompt_len=%s response_len=%s",
            len(system_prompt),
            len(response_text),
        )
        return response_text, request_payload

    async def generate_chapter(
        self,
        *,
        prompt: str | None,
        messages: list[RetrievalMessage],
        query: str,
        sources: str,
        template_text: str,
        chapter_title: str,
        chapter_index: int,
        chapter_count: int,
        model_id: str | None,
        injected_prompt: str | None = None,
    ) -> tuple[str, list[dict[str, str]]]:
        system_prompt = self._compose_system_prompt(
            (prompt or "").strip() or _DEFAULT_CHAPTER_PROMPT,
            injected_prompt,
            None,
        )
        user_text = (
            f"Section {chapter_index} of {chapter_count}: {chapter_title}\n\n"
            f"User request:\n{query}\n\n"
            f"Template:\n{template_text}\n\n"
            f"Sources:\n{sources}"
        )
        request_payload = build_prompt_payload(
            system_prompt=system_prompt,
            messages=messages,
            user_text=user_text,
        )
        response_text = await self._invoke_prompt(
            system_prompt=system_prompt,
            messages=messages,
            user_text=user_text,
            model_id=model_id,
        )
        logger.debug(
            "rag.longform.chapter title_len=%s response_len=%s",
            len(chapter_title),
            len(response_text),
        )
        return response_text, request_payload

    async def merge_sections(
        self,
        *,
        prompt: str | None,
        messages: list[RetrievalMessage],
        sources: str,
        section_text: str,
        model_id: str | None,
        injected_prompt: str | None = None,
    ) -> tuple[str, list[dict[str, str]]]:
        system_prompt = self._compose_system_prompt(
            (prompt or "").strip() or _DEFAULT_MERGE_PROMPT,
            injected_prompt,
            None,
        )
        user_text = f"Draft sections:\n{section_text}\n\nSources:\n{sources}"
        request_payload = build_prompt_payload(
            system_prompt=system_prompt,
            messages=messages,
            user_text=user_text,
        )
        response_text = await self._invoke_prompt(
            system_prompt=system_prompt,
            messages=messages,
            user_text=user_text,
            model_id=model_id,
        )
        logger.debug("rag.longform.merge response_len=%s", len(response_text))
        return response_text, request_payload

    async def stream_proofread(
        self,
        *,
        prompt: str | None,
        draft_text: str,
        session_id: str,
        message_repo,
        model_id: str | None,
        follow_up_questions_prompt: str | None = None,
        injected_prompt: str | None = None,
    ) -> AsyncIterator[str]:
        system_prompt = self._compose_system_prompt(
            (prompt or "").strip() or _DEFAULT_PROOFREAD_PROMPT,
            injected_prompt,
            follow_up_questions_prompt,
        )
        user_text = f"Draft:\n{draft_text}"
        async for delta in self._stream_prompt(
            system_prompt=system_prompt,
            user_text=user_text,
            session_id=session_id,
            message_repo=message_repo,
            model_id=model_id,
        ):
            yield delta

    async def retrieve_results(
        self,
        *,
        payload: RetrievalQueryRequest,
        tool_ctx: ToolContext,
        query_ctx: QueryContext,
    ) -> RetrievalContext:
        provider_id = tool_ctx.provider_id
        if query_ctx.mode == "answer":
            provider_id = "vertex-answer"

        retriever = self._retriever_builder(
            self._app_config,
            provider_id=provider_id,
            data_source=tool_ctx.data_source,
            policy=RetrievalPolicy(
                k=payload.top_k,
                get_extractive_answers=(
                    tool_ctx.tool.get_extractive_answers if tool_ctx.tool else False
                ),
            ),
            query_embedding=payload.query_embedding,
        )
        if retriever is None:
            raise ValueError("Unsupported RAG provider.")

        if provider_id in ("local-files", "memory"):
            await asyncio.sleep(0.8)

        documents = await retriever.ainvoke(query_ctx.search_query)
        results = documents_to_results(documents)

        search_method = resolve_search_method(tool_ctx.provider_id, payload.query_embedding)
        embedding_model = resolve_embedding_model(tool_ctx.provider_id, payload.query_embedding)
        index_name = resolve_index_name(
            self._app_config, tool_ctx.provider_id, tool_ctx.data_source
        )
        logger.debug(
            "rag.query.search provider=%s data_source=%s search_method=%s embedding_model=%s index_name=%s top_k=%s score_threshold=%s result_count=%s",
            tool_ctx.provider_id,
            tool_ctx.data_source,
            search_method,
            embedding_model,
            index_name,
            payload.top_k,
            None,
            len(results),
        )
        if not results:
            reason = resolve_zero_reason(
                provider_id=tool_ctx.provider_id,
                data_source=tool_ctx.data_source,
                query=query_ctx.search_query,
                query_embedding=payload.query_embedding,
            )
            logger.debug(
                "rag.query.zero_results provider=%s data_source=%s reason_code=%s",
                tool_ctx.provider_id,
                tool_ctx.data_source,
                reason,
            )
        return RetrievalContext(
            retriever=retriever,
            documents=documents,
            results=results,
            search_method=search_method,
            embedding_model=embedding_model,
            index_name=index_name,
        )

    def build_response_context(
        self,
        *,
        payload: RetrievalQueryRequest,
        tool_ctx: ToolContext,
        query_ctx: QueryContext,
        results: list[Any],
        message_id: str,
        text_id: str,
    ) -> ResponseContext:
        system_prompt = tool_ctx.tool.system_prompt if tool_ctx.tool else ""
        sources = format_sources(results, 1000)
        if query_ctx.mode == "simple":
            question = query_ctx.user_query
        else:
            question = query_ctx.last_user_message or query_ctx.user_query

        model_spec = self._resolve_model_spec(payload.model)
        selected_model = model_spec.model_id
        sources_payload = [
            {
                "id": f"source-{index}",
                "title": result.title or result.url,
                "url": result.url,
                "description": result.text,
            }
            for index, result in enumerate(results, start=1)
            if result.url
        ]
        result_titles = resolve_result_titles(results)
        request_payload = build_answer_payload(
            system_prompt=system_prompt,
            messages=payload.messages,
            query=question,
            sources=sources,
        )
        logger.debug(
            "rag.query.answer_payload provider=%s data_source=%s payload=%s",
            tool_ctx.provider_id,
            tool_ctx.data_source,
            preview_payload(request_payload),
        )
        retrieval_response = RetrievalQueryResponse(
            provider=tool_ctx.provider_id,
            data_source=tool_ctx.data_source,
            results=list(results),
        )
        return ResponseContext(
            system_prompt=system_prompt,
            question=question,
            retrieval_response=retrieval_response,
            sources_payload=sources_payload,
            result_titles=result_titles,
            request_payload=request_payload,
            selected_model=selected_model,
            message_id=message_id,
            text_id=text_id,
        )

    async def stream_answer(
        self,
        *,
        documents: list[Document],
        system_prompt: str,
        question: str,
        session_id: str,
        message_repo,
        follow_up_questions_prompt: str | None = None,
        injected_prompt: str | None = None,
    ) -> AsyncIterator[str]:
        model_spec = self._resolve_model_spec(None)
        llm = self._builder(self._app_config, model_spec, streaming=True).bind()

        from app.ai.chains.rag_chain import _format_docs

        context = _format_docs(documents)
        system_text = system_prompt.strip() or "Answer using the provided sources only."
        messages = [
            ("system", system_text),
            MessagesPlaceholder("history"),
            ("human", "Question: {question}\n\nSources:\n{context}"),
        ]
        prompt = ChatPromptTemplate.from_messages(messages)

        chain_with_prompt = (
            RunnableParallel(
                context=RunnableLambda(lambda x: context),
                question=RunnableLambda(lambda x: x["question"]),
                history=RunnableLambda(lambda x: x.get("history", [])),
                follow_up_questions_prompt=RunnableLambda(
                    lambda x: x.get("follow_up_questions_prompt", "")
                ),
                injected_prompt=RunnableLambda(lambda x: x.get("injected_prompt", "")),
            )
            | prompt
            | llm
        )
        history_factory = build_history_factory(
            message_repo,
            self._memory_policy,
            write_enabled=False,
        )
        chain = RunnableWithMessageHistory(
            chain_with_prompt,
            history_factory,
            input_messages_key="question",
            history_messages_key="history",
        )
        buffer = ""
        async for chunk in chain.astream(
            {
                "question": question,
                "follow_up_questions_prompt": follow_up_questions_prompt or "",
                "injected_prompt": injected_prompt or "",
            },
            config={"configurable": {"session_id": session_id}},
        ):
            delta = extract_delta(chunk)
            if not delta:
                continue
            buffer += delta
            if len(buffer) >= 8:
                yield buffer
                buffer = ""

        if buffer:
            yield buffer

    def _resolve_model_spec(self, model_id: str | None):
        return resolve_chat_model_spec(
            self._app_config,
            self._chat_caps,
            self._resolver,
            model_id,
        )

    def _compose_system_prompt(
        self,
        base_prompt: str,
        injected_prompt: str | None,
        follow_up_questions_prompt: str | None,
    ) -> str:
        parts = [base_prompt.strip()]
        if injected_prompt:
            parts.append(injected_prompt.strip())
        if follow_up_questions_prompt:
            parts.append(follow_up_questions_prompt.strip())
        return "\n\n".join(part for part in parts if part)

    async def _invoke_prompt(
        self,
        *,
        system_prompt: str,
        messages: list[RetrievalMessage],
        user_text: str,
        model_id: str | None,
    ) -> str:
        model_spec = self._resolve_model_spec(model_id)
        llm = self._builder(self._app_config, model_spec, streaming=False).bind(temperature=0.2)
        history = to_langchain_messages_from_roles(messages)
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", "{system_prompt}"),
                MessagesPlaceholder("history"),
                ("human", "{user_text}"),
            ]
        )
        chain = prompt_template | llm
        response = await chain.ainvoke(
            {"system_prompt": system_prompt, "history": history, "user_text": user_text},
        )
        return (response.content or "").strip()

    async def _stream_prompt(
        self,
        *,
        system_prompt: str,
        user_text: str,
        session_id: str,
        message_repo,
        model_id: str | None,
    ) -> AsyncIterator[str]:
        model_spec = self._resolve_model_spec(model_id)
        llm = self._builder(self._app_config, model_spec, streaming=True).bind()
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", "{system_prompt}"),
                MessagesPlaceholder("history"),
                ("human", "{user_text}"),
            ]
        )
        chain = prompt_template | llm
        history_factory = build_history_factory(
            message_repo,
            self._memory_policy,
            write_enabled=False,
        )
        stream_chain = RunnableWithMessageHistory(
            chain,
            history_factory,
            input_messages_key="user_text",
            history_messages_key="history",
        )
        buffer = ""
        async for chunk in stream_chain.astream(
            {"system_prompt": system_prompt, "user_text": user_text},
            config={"configurable": {"session_id": session_id}},
        ):
            delta = extract_delta(chunk)
            if not delta:
                continue
            buffer += delta
            if len(buffer) >= 8:
                yield buffer
                buffer = ""
        if buffer:
            yield buffer
