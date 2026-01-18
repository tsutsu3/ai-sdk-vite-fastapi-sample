import json
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from app.ai.llms.factory import build_embeddings
from app.ai.models import EmbeddingSpec, RetrievalPolicy, RetrieverSpec
from app.ai.retrievers.local_json_retriever import LocalJSONRetriever
from app.ai.retrievers.vertex_answer_retriever import VertexAnswerRetriever
from app.core.config import AppConfig


def build_retriever(
    app_config: AppConfig,
    spec: RetrieverSpec,
    policy: RetrievalPolicy,
    *,
    tenant_id: str,
    query_embedding: list[float] | None = None,
) -> BaseRetriever:
    if spec.provider == "azure-ai-search":
        return _build_azure_ai_search_retriever(app_config, spec, policy, tenant_id)
    if spec.provider == "vertex-ai-search":
        return _build_vertex_ai_search_retriever(app_config, spec, policy, tenant_id)
    if spec.provider == "vertex-answer":
        return _build_vertex_answer_retriever(app_config, policy, tenant_id)
    raise RuntimeError(f"Unsupported retriever provider: {spec.provider}")


def build_retriever_for_provider(
    app_config: AppConfig,
    *,
    provider_id: str,
    data_source: str,
    policy: RetrievalPolicy,
    tenant_id: str,
    query_embedding: list[float] | None = None,
) -> BaseRetriever:
    normalized = provider_id.strip().lower()
    if normalized == "vertex-search":
        return build_retriever(
            app_config,
            RetrieverSpec(provider="vertex-ai-search", data_source=data_source),
            policy,
            tenant_id=tenant_id,
        )
    if normalized == "vertex-answer":
        # Direct Discovery Engine API for answer mode
        return build_retriever(
            app_config,
            RetrieverSpec(provider="vertex-answer", data_source=data_source),
            policy,
            tenant_id=tenant_id,
        )
    if normalized == "ai-search":
        if not app_config.embeddings_provider or not app_config.embeddings_model:
            raise RuntimeError("Embeddings are not configured for Azure AI Search.")
        return build_retriever(
            app_config,
            RetrieverSpec(
                provider="azure-ai-search",
                data_source=data_source,
                embeddings=EmbeddingSpec(
                    provider=app_config.embeddings_provider,
                    model_id=app_config.embeddings_model,
                ),
            ),
            policy,
            tenant_id=tenant_id,
        )

    if normalized in {"memory", "local-files"}:
        if normalized == "local-files":
            return _build_local_files_retriever(
                app_config, policy, data_source, tenant_id=tenant_id
            )
        return _build_memory_retriever(app_config, policy, data_source, tenant_id=tenant_id)
    raise RuntimeError(f"Unsupported provider id: {provider_id}")


def _build_search_kwargs(
    policy: RetrievalPolicy,
    *,
    filter_expression: str | None = None,
) -> dict[str, object]:
    search_kwargs: dict[str, object] = {"k": policy.k}
    if policy.score_threshold is not None:
        search_kwargs["score_threshold"] = policy.score_threshold
    if policy.mmr:
        search_kwargs["search_type"] = "mmr"
    if filter_expression:
        search_kwargs["filter"] = filter_expression
    return search_kwargs


def _build_azure_ai_search_retriever(
    app_config: AppConfig,
    spec: RetrieverSpec,
    policy: RetrievalPolicy,
    tenant_id: str,
) -> BaseRetriever:
    try:
        from langchain_community.vectorstores.azuresearch import AzureSearch
    except ImportError as exc:
        raise RuntimeError("langchain-community is required for Azure AI Search.") from exc
    if not app_config.retrieval_ai_search_url or not app_config.retrieval_ai_search_api_key:
        raise RuntimeError("Azure AI Search settings are not configured.")
    filter_expression = _build_ai_search_filter_expression(
        app_config, spec, tenant_id=tenant_id
    )
    if spec.embeddings is None:
        raise RuntimeError("Embeddings are required for Azure AI Search.")
    embeddings = build_embeddings(app_config, spec.embeddings)
    vector_store = AzureSearch(
        azure_search_endpoint=app_config.retrieval_ai_search_url,
        azure_search_key=app_config.retrieval_ai_search_api_key,
        index_name=spec.data_source,
        embedding_function=embeddings,
    )
    return vector_store.as_retriever(
        search_kwargs=_build_search_kwargs(policy, filter_expression=filter_expression)
    )


def _build_vertex_ai_search_retriever(
    app_config: AppConfig,
    spec: RetrieverSpec,
    policy: RetrievalPolicy,
    tenant_id: str,
) -> BaseRetriever:
    try:
        from langchain_google_community.vertex_ai_search import (
            VertexAISearchRetriever,
        )
    except ImportError as exc:
        raise RuntimeError(
            "langchain-google-community is required for Vertex AI Search."
        ) from exc
    return VertexAISearchRetriever(
        project_id=app_config.vertex_search_project_id,
        location_id=app_config.vertex_search_location,
        data_store_id=app_config.vertex_search_data_store,
        serving_config_id=app_config.vertex_search_serving_config,
        engine_data_type=0,
        filter=_build_vertex_search_filter_expression(
            app_config,
            spec,
            tenant_id=tenant_id,
        ),
        max_documents=policy.k,
        get_extractive_answers=policy.get_extractive_answers,
    )


def _build_vertex_search_filter_expression(
    app_config: AppConfig,
    spec: RetrieverSpec,
    tenant_id: str,
) -> str | None:
    template = (app_config.vertex_search_filter_template or "").strip()
    if not template:
        raise RuntimeError("VERTEX_SEARCH_FILTER_TEMPLATE is required for tenancy.")
    if "{tenant_id}" not in template:
        raise RuntimeError("VERTEX_SEARCH_FILTER_TEMPLATE must include '{tenant_id}'.")
    try:
        return template.format(data_source=spec.data_source, tenant_id=tenant_id)
    except Exception as exc:  # pragma: no cover - defensive format guard
        raise RuntimeError("Invalid Vertex Search filter template.") from exc


def _build_ai_search_filter_expression(
    app_config: AppConfig,
    spec: RetrieverSpec,
    tenant_id: str,
) -> str | None:
    template = (app_config.retrieval_ai_search_filter_template or "").strip()
    if not template:
        raise RuntimeError("RETRIEVAL_AI_SEARCH_FILTER_TEMPLATE is required for tenancy.")
    if "{tenant_id}" not in template:
        raise RuntimeError("RETRIEVAL_AI_SEARCH_FILTER_TEMPLATE must include '{tenant_id}'.")
    try:
        return template.format(data_source=spec.data_source, tenant_id=tenant_id)
    except Exception as exc:  # pragma: no cover - defensive format guard
        raise RuntimeError("Invalid Azure AI Search filter template.") from exc


def _build_vertex_answer_retriever(
    app_config: AppConfig,
    policy: RetrievalPolicy,
    tenant_id: str,
) -> BaseRetriever:
    if tenant_id:
        raise RuntimeError("Vertex Answer retrieval requires tenant-scoped filtering.")
    return VertexAnswerRetriever(
        project_id=app_config.vertex_search_project_id or app_config.gcp_project_id,
        location=app_config.vertex_search_location,
        engine_id=app_config.vertex_search_data_store,
        serving_config=app_config.vertex_search_serving_config,
        max_documents=policy.k,
    )


def _build_local_files_retriever(
    app_config: AppConfig,
    policy: RetrievalPolicy,
    data_source: str,
    *,
    tenant_id: str,
) -> BaseRetriever:
    json_path = _get_local_json_path(app_config.retrieval_local_path, data_source)
    return LocalJSONRetriever(
        json_path=json_path,
        k=policy.k,
        min_score=policy.score_threshold or 0.0,
        tenant_id=tenant_id,
    )


def _build_memory_retriever(
    app_config: AppConfig,
    policy: RetrievalPolicy,
    data_source: str,
    *,
    tenant_id: str,
) -> BaseRetriever:
    try:
        from langchain_community.vectorstores.inmemory import InMemoryVectorStore
    except ImportError as exc:
        raise RuntimeError("langchain-community is required for InMemoryVectorStore.") from exc
    embeddings = _build_memory_embeddings(app_config)
    documents = _build_memory_documents(app_config, data_source, tenant_id=tenant_id)
    vector_store = InMemoryVectorStore.from_documents(documents, embedding=embeddings)
    return vector_store.as_retriever(search_kwargs=_build_search_kwargs(policy))


def _build_memory_embeddings(app_config: AppConfig):
    if app_config.embeddings_provider and app_config.embeddings_model:
        return build_embeddings(
            app_config,
            EmbeddingSpec(
                provider=app_config.embeddings_provider,
                model_id=app_config.embeddings_model,
            ),
        )
    try:
        from langchain_community.embeddings.fake import FakeEmbeddings
    except ImportError as exc:
        raise RuntimeError("Embeddings settings are required without FakeEmbeddings.") from exc
    return FakeEmbeddings(size=1536)


def _build_memory_documents(
    app_config: AppConfig,
    data_source: str,
    *,
    tenant_id: str,
) -> list[Document]:
    if data_source:
        json_path = _get_local_json_path(app_config.retrieval_local_path, data_source)
        json_docs = _load_json_documents(json_path, tenant_id=tenant_id)
        if json_docs:
            return json_docs
    return []


def _get_local_json_path(base_path: str, data_source: str) -> str:
    """Get path to JSON file for local retrieval.

    Args:
        base_path: Base retrieval path.
        data_source: Data source identifier (e.g., tool0101).

    Returns:
        Absolute path to documents.json file.
    """
    base = Path(base_path)

    # If base_path is relative, resolve it relative to the project root
    if not base.is_absolute():
        # Get the project root (4 levels up from this file: factory.py -> retrievers -> ai -> app -> backend)
        project_root = Path(__file__).resolve().parents[4]
        base = project_root / base

    if data_source:
        json_file = base / data_source / "documents.json"
    else:
        json_file = base / "documents.json"

    return str(json_file.resolve())


def _load_json_documents(json_path: str, *, tenant_id: str) -> list[Document]:
    path = Path(json_path)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(data, dict) and "documents" in data:
        data = data["documents"]
    if not isinstance(data, list):
        return []
    documents: list[Document] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        raw_tenant = item.get("tenant_id") or item.get("tenantId")
        if raw_tenant != tenant_id:
            continue
        documents.append(
            Document(
                page_content=item.get("content", ""),
                metadata={
                    "id": item.get("id", ""),
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "tags": item.get("tags", []),
                    "category": item.get("category", ""),
                    "tenant_id": raw_tenant,
                },
            )
        )
    return documents


def _load_local_documents(
    base_path: str,
    data_source: str,
    *,
    tenant_id: str,
) -> list[Document]:
    base = Path(base_path)
    target = (base / data_source).resolve() if data_source else base.resolve()
    if not target.exists() or not target.is_dir():
        return []
    allowed = {".txt", ".md", ".csv", ".json", ".html", ".log"}
    docs: list[Document] = []
    for path in target.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in allowed:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if not text:
            continue
        docs.append(
            Document(
                page_content=text[:2000],
                metadata={
                    "url": str(path.relative_to(base)),
                    "title": path.name,
                    "tenant_id": tenant_id,
                },
            )
        )
        if len(docs) >= 200:
            break
    return docs
