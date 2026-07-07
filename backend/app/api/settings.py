from fastapi import APIRouter

from app.features.settings.schemas import ModelSettingsUpdate, ModelTestRequest
from app.features.settings.service import get_model_settings, reset_model_settings, update_model_settings
from app.services.qwen_client import test_model_connection


router = APIRouter()


@router.get("/settings/models")
def read_model_settings() -> dict[str, object]:
    return get_model_settings()


@router.put("/settings/models")
def write_model_settings(payload: ModelSettingsUpdate) -> dict[str, object]:
    return update_model_settings(payload)


@router.post("/settings/models/reset")
def reset_models() -> dict[str, object]:
    return reset_model_settings()


@router.post("/settings/models/test")
def test_model(payload: ModelTestRequest) -> dict[str, object]:
    return test_model_connection(
        provider=payload.provider,
        model=payload.model,
        config_id=payload.config_id,
        config_name=payload.config_name,
        base_url=payload.base_url,
        api_key_override=payload.api_key,
        timeout_seconds=payload.timeout_seconds,
    )
