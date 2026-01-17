from fastapi import APIRouter, Depends

from app.core.config import AppConfig, ChatCapabilities
from app.core.dependencies import get_app_config, get_chat_capabilities
from app.features.capabilities.schemas import (
    APIPageSizeCapability,
    CapabilitiesResponse,
    ModelCapability,
)

router = APIRouter()


@router.get(
    "/capabilities",
    response_model=CapabilitiesResponse,
    tags=["Capabilities"],
    summary="Get app capabilities",
    description="Lists enabled chat models",
    response_description="Capabilities available to the frontend.",
    responses={
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["query", "include"],
                                "msg": "Input should be a valid boolean",
                                "type": "bool_parsing",
                            }
                        ]
                    }
                }
            },
        }
    },
)
def get_capabilities(
    app_config: AppConfig = Depends(get_app_config),
    capabilities: ChatCapabilities = Depends(get_chat_capabilities),
) -> CapabilitiesResponse:
    """Return capabilities.

    Lists enabled chat models.
    """
    models: list[ModelCapability] = []
    for provider_id in sorted(capabilities.providers):
        for model_id in sorted(capabilities.providers.get(provider_id, set())):
            models.append(
                ModelCapability(
                    id=model_id,
                    name=capabilities.model_names.get(model_id, model_id),
                    chef=capabilities.model_chefs.get(model_id, provider_id.title()),
                    chef_slug=capabilities.model_chef_slugs.get(model_id, provider_id),
                    providers=capabilities.model_providers.get(model_id, [provider_id]),
                )
            )

    model_ids = [model.id for model in models]
    default_model = app_config.chat_default_model
    if not default_model or default_model not in model_ids:
        default_model = model_ids[0] if model_ids else ""

    return CapabilitiesResponse(
        models=models,
        defaultModel=default_model,
        apiPageSizes=APIPageSizeCapability(
            messagesPageSizeDefault=app_config.messages_page_default_limit,
            messagesPageSizeMax=app_config.messages_page_max_limit,
            conversationsPageSizeDefault=app_config.conversations_page_default_limit,
            conversationsPageSizeMax=app_config.conversations_page_max_limit,
        ),
    )
