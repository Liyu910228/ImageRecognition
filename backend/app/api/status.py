from fastapi import APIRouter

from app.core.config import settings
from app.features.settings.service import get_model_settings
from app.features.templates.repository import get_template_status, list_template_sources


router = APIRouter()


@router.get("/status")
def status() -> dict[str, object]:
    template_status = get_template_status(settings.template_manifest_path, settings.vector_index_path)
    template_status["sources"] = list_template_sources(settings.template_sources_dir)
    model_settings = get_model_settings()
    return {
        "service": "ready",
        "models": {
            "embeddingModel": model_settings["embedding_model"],
            "defaultModelPlatform": model_settings.get("default_model_platform", "aliyun"),
            "vlModel": model_settings["vl_model"],
            "apiKeyConfigured": bool(model_settings["api_key_configured"]),
            "volcApiKeyConfigured": bool(model_settings.get("volc_api_key_configured", False)),
            "source": model_settings["source"],
        },
        "templates": template_status,
    }
