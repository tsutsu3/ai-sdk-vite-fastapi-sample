from typing import Any

from langchain_core.documents import Document
from pydantic import BaseModel, ConfigDict

from app.features.authz.models import TenantRecord, UserRecord
from app.features.retrieval.schemas import RetrievalQueryResponse
from app.features.retrieval.tools import RetrievalToolSpec


class AuthContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    tenant_id: str
    user_id: str
    user_record: UserRecord
    tenant_record: TenantRecord


class ToolContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    tool: RetrievalToolSpec | None
    data_source: str
    provider_id: str
    tool_id_for_conversation: str
    tenant_id: str


class QueryContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    mode: str
    user_query: str
    search_query: str
    last_user_message: str


class ConversationContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    conversation_id: str
    title: str
    should_generate_title: bool
    user_message_text: str


class RetrievalContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    retriever: Any
    documents: list[Document]
    results: list[Any]
    search_method: str
    embedding_model: str | None
    index_name: str


class ResponseContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    system_prompt: str
    question: str
    retrieval_response: RetrievalQueryResponse
    sources_payload: list[dict[str, str]]
    result_titles: list[str]
    request_payload: list[dict[str, str]]
    selected_model: str | None
    message_id: str
    text_id: str
