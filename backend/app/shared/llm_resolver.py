from app.ai.models import ChatModelSpec
from app.ai.ports import ChatModelResolver
from app.core.config import AppConfig, ChatCapabilities


def resolve_chat_model_spec(
    app_config: AppConfig,
    chat_caps: ChatCapabilities,
    resolver: ChatModelResolver,
    model_id: str | None,
) -> ChatModelSpec:
    selected_model = model_id or app_config.chat_default_model or None
    if not selected_model:
        candidates = {model for models in chat_caps.providers.values() for model in models}
        if len(candidates) == 1:
            selected_model = next(iter(candidates))
    return resolver(chat_caps, selected_model, default_model_id=selected_model)
