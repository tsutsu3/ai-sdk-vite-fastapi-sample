"""Vertex AI Search Answer Retriever using Discovery Engine SDK.

This retriever uses the Discovery Engine ConversationalSearchService
to perform search + answer in a single API call, bypassing LangChain.
"""

import logging

from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field

logger = logging.getLogger(__name__)


class VertexAnswerRetriever(BaseRetriever):
    """Vertex AI Search retriever using answer_query for single-pass search+answer.

    This retriever directly calls the Discovery Engine AnswerQuery API,
    which performs semantic search and generates an LLM answer in one call.
    """

    project_id: str = Field(description="GCP project ID")
    location: str = Field(default="global", description="Location (global, us, eu, etc.)")
    engine_id: str = Field(description="Discovery Engine / Vertex AI Search engine ID")
    serving_config: str = Field(
        default="default_serving_config", description="Serving config name"
    )
    include_citations: bool = Field(default=True, description="Include citations in answer")
    answer_language_code: str = Field(default="en", description="Language code for answer")
    max_documents: int = Field(default=5, ge=1, description="Maximum documents to return")

    def _get_relevant_documents(self, query: str) -> list[Document]:
        """Retrieve documents using Vertex AI Search answer_query API.

        Args:
            query: User query string.

        Returns:
            List of Document objects with answer text and citations.
        """
        logger.info(
            "vertex_answer.query query=%s project=%s engine=%s",
            query[:100],
            self.project_id,
            self.engine_id,
        )

        # Setup client with location-specific endpoint
        client_options = None
        if self.location != "global":
            endpoint = f"{self.location}-discoveryengine.googleapis.com"
            client_options = ClientOptions(api_endpoint=endpoint)

        client = discoveryengine.ConversationalSearchServiceClient(client_options=client_options)

        # Build serving config resource name
        serving_config_name = (
            f"projects/{self.project_id}/locations/{self.location}/"
            f"collections/default_collection/engines/{self.engine_id}/"
            f"servingConfigs/{self.serving_config}"
        )

        # Configure answer generation
        answer_generation_spec = discoveryengine.AnswerQueryRequest.AnswerGenerationSpec(
            include_citations=self.include_citations,
            answer_language_code=self.answer_language_code,
        )

        # Build request
        request = discoveryengine.AnswerQueryRequest(
            serving_config=serving_config_name,
            query=discoveryengine.Query(text=query),
            answer_generation_spec=answer_generation_spec,
        )

        # Call API
        try:
            response = client.answer_query(request)
            logger.info(
                "vertex_answer.response answer_length=%d citations=%d",
                len(response.answer.answer_text) if response.answer else 0,
                len(response.answer.citations) if response.answer else 0,
            )
        except Exception as exc:
            logger.error("vertex_answer.error error=%s", exc, exc_info=True)
            raise

        # Convert response to LangChain Documents
        documents = self._parse_response(response)
        logger.info("vertex_answer.complete documents=%d", len(documents))
        return documents

    def _parse_response(self, response: discoveryengine.AnswerQueryResponse) -> list[Document]:
        """Parse AnswerQueryResponse into LangChain Documents.

        Args:
            response: API response from answer_query.

        Returns:
            List of Document objects.
        """
        documents = []

        if not response.answer:
            logger.warning("vertex_answer.no_answer")
            return documents

        answer = response.answer
        answer_text = answer.answer_text or ""

        # Main answer document
        main_doc = Document(
            page_content=answer_text,
            metadata={
                "type": "answer",
                "state": answer.state.name if answer.state else "UNKNOWN",
            },
        )
        documents.append(main_doc)

        # Add citation documents
        for idx, citation in enumerate(answer.citations or []):
            for source in citation.sources or []:
                # Extract reference from structured document data
                reference_id = ""
                reference_uri = ""

                if source.reference_id:
                    reference_id = source.reference_id

                # Try to get URI from structured data if available
                structured_data = getattr(source, "structured_data", None)
                if structured_data:
                    # Convert struct to dict
                    data_dict = dict(structured_data)
                    reference_uri = data_dict.get("uri", "") or data_dict.get("url", "")

                doc = Document(
                    page_content=citation.text or "",
                    metadata={
                        "type": "citation",
                        "citation_index": idx,
                        "reference_id": reference_id,
                        "url": reference_uri,
                        "title": reference_id,  # Fallback to reference_id for title
                    },
                )
                documents.append(doc)

        return documents

    async def _aget_relevant_documents(self, query: str) -> list[Document]:
        """Async version (fallback to sync)."""
        return self._get_relevant_documents(query)
