from fastapi import HTTPException

from app.features.authz.request_context import (
    get_current_tenant_id,
    get_current_tenant_record,
    get_current_user_id,
    get_current_user_record,
)
from app.features.authz.tool_merge import merge_tools
from app.features.retrieval.run.models import AuthContext, QueryContext, ToolContext
from app.features.retrieval.run.utils import (
    extract_last_user_message,
    is_authorized_for_source,
)
from app.features.retrieval.schemas import RetrievalQueryRequest
from app.features.retrieval.tools import RetrievalToolSpec, resolve_tool


class QueryPlanner:
    """Resolve auth, tool, and query planning contexts for RAG."""

    def __init__(self, execution_service) -> None:
        self._execution = execution_service

    def require_auth_context(self) -> AuthContext:
        user_record = get_current_user_record()
        tenant_record = get_current_tenant_record()
        if user_record is None or tenant_record is None:
            raise HTTPException(status_code=403, detail="User is not authorized")
        return AuthContext(
            tenant_id=get_current_tenant_id(),
            user_id=get_current_user_id(),
            user_record=user_record,
            tenant_record=tenant_record,
        )

    def resolve_tool_context(
        self,
        payload: RetrievalQueryRequest,
        auth_ctx: AuthContext,
    ) -> ToolContext:
        tool = resolve_tool(payload.tool_id)
        data_source = tool.data_source if tool else payload.data_source
        tools = merge_tools(
            auth_ctx.tenant_record.default_tools,
            auth_ctx.user_record.tool_overrides,
        )
        authorize_target = tool.id if tool else data_source
        if not is_authorized_for_source(authorize_target, tools):
            raise HTTPException(status_code=403, detail="Not authorized for this data source.")

        provider_id = (tool.provider if tool and tool.provider else payload.provider) or ""
        provider_id = provider_id.strip().lower()
        if not provider_id:
            raise HTTPException(status_code=400, detail="Retrieval provider is required.")

        tool_id_for_conversation = (
            tool.id if tool else payload.tool_id if payload.tool_id else data_source or "rag"
        )
        return ToolContext(
            tool=tool,
            data_source=data_source,
            provider_id=provider_id,
            tool_id_for_conversation=tool_id_for_conversation,
        )

    async def resolve_query_context(
        self,
        payload: RetrievalQueryRequest,
        tool: RetrievalToolSpec | None,
    ) -> QueryContext:
        mode = payload.mode or (tool.mode if tool else "simple")
        user_query = payload.query.strip()
        last_user = extract_last_user_message(payload.messages)
        if last_user:
            user_query = last_user
        search_query = user_query
        if payload.hyde_enabled and mode != "answer":
            hyde_query = await self._execution.generate_hypothetical_answer(
                messages=payload.messages,
                query=user_query,
                hyde_prompt=tool.hyde_prompt if tool else None,
            )
            if hyde_query:
                search_query = hyde_query
        elif mode == "chat" and tool and tool.query_prompt:
            generated = await self._execution.generate_search_query(
                prompt=tool.query_prompt,
                messages=payload.messages,
                query=user_query,
            )
            if generated and generated != "0":
                search_query = generated
        return QueryContext(
            mode=mode,
            user_query=user_query,
            search_query=search_query,
            last_user_message=last_user,
        )
