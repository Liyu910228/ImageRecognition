from __future__ import annotations

from app.core.config import settings
from app.features.recognition.product_tags import DEFAULT_SNOW_BRANDS
from app.features.settings.defaults import DEFAULT_CR_SNOW_VISION_PROMPT
from app.features.settings.repository import delete_json_settings, load_json_settings, save_json_settings
from app.features.settings.schemas import ModelSettingsUpdate

NODE_MODEL_KEYS = ("default", "brand_package", "ocr_text", "final_judge")


def _node_models(model: str, value: object = None) -> dict[str, str]:
    fallback = str(model or settings.qwen_vl_model).strip()
    raw = value if isinstance(value, dict) else {}
    return {
        key: str(raw.get(key) or fallback).strip() or fallback
        for key in NODE_MODEL_KEYS
    }


def _default_model_configs() -> list[dict[str, object]]:
    aliyun_model = settings.qwen_vl_model
    volc_model = "ep-your-volc-model"
    return [
        {
            "id": "default",
            "name": "默认模型",
            "enabled": True,
            "provider": "aliyun",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            "model": aliyun_model,
            "node_models": _node_models(aliyun_model),
            "api_key": "",
            "use_as_default": True,
        },
        {
            "id": "volc_default",
            "name": "火山模型",
            "enabled": False,
            "provider": "volc",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
            "model": volc_model,
            "node_models": _node_models(volc_model),
            "api_key": "",
            "use_as_default": False,
        },
    ]


def _default_settings() -> dict[str, object]:
    return {
        "embedding_model": settings.qwen_embedding_model,
        "default_model_platform": "aliyun",
        "vl_model": settings.qwen_vl_model,
        "task_model_profile": "default",
        "model_profiles": "",
        "business_strategies": [],
        "model_configs": _public_model_configs(_default_model_configs(), "", ""),
        "enable_vl_rerank": True,
        "low_confidence_threshold": settings.low_confidence_threshold,
        "top_k": 5,
        "qwen_timeout_seconds": 10,
        "weight_brand_match_visual": 0.2,
        "weight_brand_match_brand": 0.55,
        "weight_brand_match_text": 0.25,
        "weight_brand_miss_visual": 0.8,
        "weight_brand_miss_text": 0.2,
        "weight_no_brand_visual": 0.85,
        "weight_no_brand_text": 0.15,
        "snow_brand_names": "\n".join(DEFAULT_SNOW_BRANDS),
        "vision_prompt": DEFAULT_CR_SNOW_VISION_PROMPT,
        "dashscope_api_key": "",
        "volc_api_key": "",
        "source": "env",
        "api_key_configured": bool(settings.dashscope_api_key),
        "volc_api_key_configured": False,
        "embedding_index_needs_rebuild": False,
    }


def get_model_settings() -> dict[str, object]:
    stored = load_json_settings(settings.model_settings_path)
    if not stored:
        return _default_settings()

    current_embedding_model = str(stored.get("embedding_model", settings.qwen_embedding_model))
    stored_key = str(stored.get("dashscope_api_key", "") or "")
    stored_volc_key = str(stored.get("volc_api_key", "") or "")
    display_settings = {**stored}
    runtime_configs = _runtime_model_configs(stored)
    if not str(display_settings.get("vision_prompt", "") or "").strip():
        display_settings["vision_prompt"] = DEFAULT_CR_SNOW_VISION_PROMPT
    return {
        **_default_settings(),
        **display_settings,
        "business_strategies": [],
        "model_configs": _public_model_configs(runtime_configs, stored_key, stored_volc_key),
        "task_model_profile": _default_model_config_id(runtime_configs),
        "model_profiles": "",
        "source": "runtime",
        "dashscope_api_key": "",
        "volc_api_key": "",
        "api_key_configured": bool(stored_key or settings.dashscope_api_key),
        "volc_api_key_configured": bool(stored_volc_key),
        "embedding_index_needs_rebuild": current_embedding_model != settings.qwen_embedding_model,
    }


def update_model_settings(payload: ModelSettingsUpdate) -> dict[str, object]:
    existing = load_json_settings(settings.model_settings_path) or {}
    next_settings = payload.model_dump()
    next_settings["business_strategies"] = []
    next_settings["task_model_profile"] = _default_model_config_id(next_settings.get("model_configs", []))
    next_settings["model_profiles"] = ""
    next_settings["model_configs"] = _merge_incoming_model_configs(
        next_settings.get("model_configs", []),
        existing.get("model_configs", []),
    )
    incoming_key = (next_settings.pop("dashscope_api_key", None) or "").strip()
    incoming_volc_key = (next_settings.pop("volc_api_key", None) or "").strip()
    if incoming_key:
        next_settings["dashscope_api_key"] = incoming_key
    elif existing.get("dashscope_api_key"):
        next_settings["dashscope_api_key"] = existing["dashscope_api_key"]
    if incoming_volc_key:
        next_settings["volc_api_key"] = incoming_volc_key
    elif existing.get("volc_api_key"):
        next_settings["volc_api_key"] = existing["volc_api_key"]
    save_json_settings(settings.model_settings_path, next_settings)
    return get_model_settings()


def get_model_runtime_configs() -> list[dict[str, object]]:
    stored = load_json_settings(settings.model_settings_path) or {}
    return _runtime_model_configs(stored)


def get_effective_api_key(api_key_override: str | None = None, provider: str = "aliyun") -> tuple[str, str]:
    normalized_provider = _normalize_provider(provider)
    if api_key_override and api_key_override.strip() and normalized_provider == "aliyun":
        return api_key_override.strip(), "aliyun:request"
    stored = load_json_settings(settings.model_settings_path) or {}
    if normalized_provider == "volc":
        stored_key = str(stored.get("volc_api_key", "") or "").strip()
        if stored_key:
            return stored_key, "volc:runtime"
        return "", "volc:none"
    stored_key = str(stored.get("dashscope_api_key", "") or "").strip()
    if stored_key:
        return stored_key, "aliyun:runtime"
    if settings.dashscope_api_key:
        return settings.dashscope_api_key, "aliyun:env"
    return "", "aliyun:none"


def get_default_runtime_model_config() -> dict[str, object] | None:
    configs = get_model_runtime_configs()
    enabled = [item for item in configs if bool(item.get("enabled", True))]
    return next((item for item in enabled if bool(item.get("use_as_default", False))), None) or (enabled[0] if enabled else (configs[0] if configs else None))


def _default_model_config_id(configs: object) -> str:
    items = configs if isinstance(configs, list) else []
    enabled = [item for item in items if isinstance(item, dict) and bool(item.get("enabled", True))]
    active = next((item for item in enabled if bool(item.get("use_as_default", False))), None) or (enabled[0] if enabled else None)
    return str(active.get("id") or "default") if active else "default"


def _normalize_provider(provider: str) -> str:
    text = str(provider or "aliyun").strip().lower()
    if text in {"volc", "volcano", "huoshan", "ark", "doubao"}:
        return "volc"
    return "aliyun"


def _runtime_model_configs(stored: dict[str, object]) -> list[dict[str, object]]:
    legacy_aliyun_key = str(stored.get("dashscope_api_key", "") or settings.dashscope_api_key or "")
    legacy_volc_key = str(stored.get("volc_api_key", "") or "")
    raw_configs = stored.get("model_configs")
    configs = raw_configs if isinstance(raw_configs, list) and raw_configs else _default_model_configs()
    normalized: list[dict[str, object]] = []
    for index, item in enumerate(configs):
        if not isinstance(item, dict):
            continue
        provider = _normalize_provider(str(item.get("provider", "aliyun") or "aliyun"))
        default_key = legacy_volc_key if provider == "volc" else legacy_aliyun_key
        config_id = str(item.get("id") or f"model_{index + 1}").strip()
        model = str(item.get("model") or settings.qwen_vl_model).strip()
        normalized.append(
            {
                "id": config_id or f"model_{index + 1}",
                "name": str(item.get("name") or config_id or f"模型 {index + 1}").strip(),
                "enabled": bool(item.get("enabled", True)),
                "provider": provider,
                "base_url": str(item.get("base_url") or _default_provider_url(provider)).strip(),
                "model": model,
                "node_models": _node_models(model, item.get("node_models")),
                "api_key": str(item.get("api_key") or default_key).strip(),
                "use_as_default": bool(item.get("use_as_default", index == 0)),
            }
        )
    return normalized


def _public_model_configs(configs: list[dict[str, object]], aliyun_key: str, volc_key: str) -> list[dict[str, object]]:
    public: list[dict[str, object]] = []
    for item in configs:
        provider = _normalize_provider(str(item.get("provider", "aliyun") or "aliyun"))
        api_key = str(item.get("api_key") or "")
        if not api_key:
            api_key = volc_key if provider == "volc" else aliyun_key
        public.append({**item, "api_key": "", "api_key_configured": bool(api_key)})
    return public


def _merge_incoming_model_configs(
    incoming: list[dict[str, object]],
    existing: object,
) -> list[dict[str, object]]:
    existing_items = existing if isinstance(existing, list) else []
    existing_by_key: dict[str, dict[str, object]] = {}
    for item in existing_items:
        if not isinstance(item, dict):
            continue
        for key in [str(item.get("id") or ""), str(item.get("name") or "")]:
            if key:
                existing_by_key[key] = item

    merged: list[dict[str, object]] = []
    for index, item in enumerate(incoming):
        if not isinstance(item, dict):
            continue
        config_id = str(item.get("id") or f"model_{index + 1}").strip()
        name = str(item.get("name") or config_id or f"模型 {index + 1}").strip()
        previous = existing_by_key.get(config_id) or existing_by_key.get(name) or {}
        incoming_key = str(item.get("api_key") or "").strip()
        previous_key = str(previous.get("api_key") or "").strip()
        model = str(item.get("model") or settings.qwen_vl_model).strip()
        merged.append(
            {
                "id": config_id,
                "name": name,
                "enabled": bool(item.get("enabled", True)),
                "provider": _normalize_provider(str(item.get("provider", "aliyun") or "aliyun")),
                "base_url": str(item.get("base_url") or "").strip(),
                "model": model,
                "node_models": _node_models(model, item.get("node_models") or previous.get("node_models")),
                "api_key": incoming_key or previous_key,
                "use_as_default": bool(item.get("use_as_default", False)),
            }
        )
    return merged or _default_model_configs()


def _default_provider_url(provider: str) -> str:
    if _normalize_provider(provider) == "volc":
        return "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    return "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"


def reset_model_settings() -> dict[str, object]:
    delete_json_settings(settings.model_settings_path)
    return get_model_settings()
