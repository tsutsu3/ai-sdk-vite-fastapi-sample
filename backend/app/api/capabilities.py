from fastapi import APIRouter, Request

from app.features.chat.capabilities.models import CapabilitiesResponse, ModelCapability

router = APIRouter()


@router.get("/capabilities", response_model=CapabilitiesResponse)
def get_capabilities(request: Request) -> CapabilitiesResponse:
    capabilities = request.app.state.chat_capabilities
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

    return CapabilitiesResponse(models=models)
