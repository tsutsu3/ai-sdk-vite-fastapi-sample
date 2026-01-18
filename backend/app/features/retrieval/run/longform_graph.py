import asyncio
from collections.abc import Callable

from langgraph.graph import END, StateGraph
from pydantic import BaseModel, ConfigDict, Field

from app.features.retrieval.run.execution_service import RetrievalExecutionService
from app.features.retrieval.run.models import QueryContext, ToolContext
from app.features.retrieval.run.utils import format_sources
from app.features.retrieval.schemas import RetrievalQueryRequest


class LongformChapterResult(BaseModel):
    """Result payload for a single longform chapter."""

    model_config = ConfigDict(frozen=True)

    title: str
    text: str
    request_payload: list[dict[str, str]]


class LongformGraphState(BaseModel):
    """State shared across longform graph nodes."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    payload: RetrievalQueryRequest
    tool_ctx: ToolContext
    query_ctx: QueryContext
    sources_text: str
    model_id: str | None
    template_text: str = ""
    template_payload: list[dict[str, str]] = Field(default_factory=list)
    chapter_results: list[LongformChapterResult] = Field(default_factory=list)
    merged_text: str = ""
    merge_payload: list[dict[str, str]] = Field(default_factory=list)


def _default_resolve_chapter_titles(
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


def build_longform_graph(
    *,
    execution: RetrievalExecutionService,
    chapter_concurrency: int,
    resolve_chapter_titles: Callable[[list[str], str, int], list[str]] | None = None,
):
    """Build the longform generation graph (template -> chapters -> merge)."""
    resolve_chapter_titles = resolve_chapter_titles or _default_resolve_chapter_titles

    async def _generate_template(state: LongformGraphState):
        payload = state.payload
        tool_ctx = state.tool_ctx
        query_ctx = state.query_ctx
        user_query = query_ctx.last_user_message or query_ctx.user_query
        chapter_count = max(1, min(payload.chapter_count, 12))
        template_prompt = payload.template_prompt or (
            tool_ctx.tool.template_prompt if tool_ctx.tool else None
        )
        template_text, template_payload = await execution.generate_template(
            prompt=template_prompt,
            messages=payload.messages,
            query=user_query,
            sources=state.sources_text,
            chapter_count=chapter_count,
            model_id=state.model_id,
            injected_prompt=payload.injected_prompt,
        )
        return {
            "template_text": template_text,
            "template_payload": template_payload,
        }

    async def _generate_chapters(state: LongformGraphState):
        payload = state.payload
        tool_ctx = state.tool_ctx
        query_ctx = state.query_ctx
        user_query = query_ctx.last_user_message or query_ctx.user_query
        chapter_prompt = payload.chapter_prompt or (
            tool_ctx.tool.chapter_prompt if tool_ctx.tool else None
        )
        chapter_count = max(1, min(payload.chapter_count, 12))
        chapter_titles = resolve_chapter_titles(
            payload.chapter_titles,
            state.template_text,
            chapter_count,
        )
        chapter_count = len(chapter_titles)
        semaphore = asyncio.Semaphore(max(1, chapter_concurrency))

        async def _run_chapter(index: int, title: str):
            async with semaphore:
                text, request_payload = await execution.generate_chapter(
                    prompt=chapter_prompt,
                    messages=payload.messages,
                    query=user_query,
                    sources=state.sources_text,
                    template_text=state.template_text,
                    chapter_title=title,
                    chapter_index=index,
                    chapter_count=chapter_count,
                    model_id=state.model_id,
                    injected_prompt=payload.injected_prompt,
                )
                return index, LongformChapterResult(
                    title=title,
                    text=text,
                    request_payload=request_payload,
                )

        tasks = [
            asyncio.create_task(_run_chapter(index, title))
            for index, title in enumerate(chapter_titles, start=1)
        ]
        results = await asyncio.gather(*tasks)
        results.sort(key=lambda item: item[0])
        chapter_results = [result for _, result in results]
        return {"chapter_results": chapter_results}

    async def _merge_sections(state: LongformGraphState):
        payload = state.payload
        tool_ctx = state.tool_ctx
        merge_prompt = payload.merge_prompt or (
            tool_ctx.tool.merge_prompt if tool_ctx.tool else None
        )
        section_text = "\n\n".join(
            f"{result.title}\n{result.text}".strip() for result in state.chapter_results
        )
        merged_text, merge_payload = await execution.merge_sections(
            prompt=merge_prompt,
            messages=payload.messages,
            sources=state.sources_text,
            section_text=section_text,
            model_id=state.model_id,
            injected_prompt=payload.injected_prompt,
        )
        return {"merged_text": merged_text, "merge_payload": merge_payload}

    graph = StateGraph(LongformGraphState)
    graph.add_node("template", _generate_template)
    graph.add_node("chapters", _generate_chapters)
    graph.add_node("merge", _merge_sections)
    graph.set_entry_point("template")
    graph.add_edge("template", "chapters")
    graph.add_edge("chapters", "merge")
    graph.add_edge("merge", END)
    return graph.compile()


def build_longform_state(
    *,
    payload: RetrievalQueryRequest,
    tool_ctx: ToolContext,
    query_ctx: QueryContext,
    results: list[object],
    model_id: str | None,
) -> LongformGraphState:
    """Initialize longform graph state with retrieval outputs."""
    sources_text = format_sources(results, 1000)
    return LongformGraphState(
        payload=payload,
        tool_ctx=tool_ctx,
        query_ctx=query_ctx,
        sources_text=sources_text,
        model_id=model_id,
    )
