from fastapi import APIRouter, Request

from app.features.chat.capabilities.schemas import (
    APIPageSizeCapability,
    CapabilitiesResponse,
    ModelCapability,
    WebSearchEngineCapability,
)

router = APIRouter()


@router.get(
    "/capabilities",
    response_model=CapabilitiesResponse,
    tags=["Capabilities"],
    summary="Get app capabilities",
    description="Lists enabled chat models and web search engines.",
    response_description="Capabilities available to the frontend.",
)
def get_capabilities(request: Request) -> CapabilitiesResponse:
    """Return chat and web search capabilities.

    Lists enabled chat models and available web search engines.
    """
    capabilities = request.app.state.chat_capabilities
    web_search = request.app.state.web_search_service
    app_config = request.app.state.app_config
    models: list[ModelCapability] = []

    if capabilities.has_provider("memory"):
        models.append(
            ModelCapability(
                id="dummy",
                name=capabilities.model_names.get("dummy", "Dummy Memory Model"),
                chef=capabilities.model_chefs.get("dummy", "Memory"),
                chef_slug=capabilities.model_chef_slugs.get("dummy", "memory"),
                providers=capabilities.model_providers.get("dummy", ["memory"]),
            )
        )

    if capabilities.has_provider("azure"):
        for model_id in sorted(capabilities.providers.get("azure", set())):
            models.append(
                ModelCapability(
                    id=model_id,
                    name=capabilities.model_names.get(model_id, model_id),
                    chef=capabilities.model_chefs.get(model_id, "Azure"),
                    chef_slug=capabilities.model_chef_slugs.get(model_id, "azure"),
                    providers=capabilities.model_providers.get(model_id, ["azure"]),
                )
            )

    if capabilities.has_provider("ollama"):
        for model_id in sorted(capabilities.providers.get("ollama", set())):
            models.append(
                ModelCapability(
                    id=model_id,
                    name=capabilities.model_names.get(model_id, model_id),
                    chef=capabilities.model_chefs.get(model_id, "Ollama"),
                    chef_slug=capabilities.model_chef_slugs.get(model_id, "ollama"),
                    providers=capabilities.model_providers.get(model_id, ["ollama"]),
                )
            )

    web_search_engines = [
        WebSearchEngineCapability(id=engine.id, name=engine.name)
        for engine in web_search.available_engines()
    ]
    model_ids = [model.id for model in models]
    default_model = app_config.chat_default_model
    if not default_model or default_model not in model_ids:
        default_model = model_ids[0] if model_ids else ""

    return CapabilitiesResponse(
        models=models,
        defaultModel=default_model,
        webSearchEngines=web_search_engines,
        defaultWebSearchEngine=web_search.default_engine,
        apiPageSizes=APIPageSizeCapability(
            messagesPageSizeDefault=app_config.messages_page_default_limit,
            messagesPageSizeMax=app_config.messages_page_max_limit,
            conversationsPageSizeDefault=app_config.conversations_page_default_limit,
            conversationsPageSizeMax=app_config.conversations_page_max_limit,
        ),
    )
