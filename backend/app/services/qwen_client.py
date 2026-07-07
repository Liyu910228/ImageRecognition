from __future__ import annotations

import base64
import json
import mimetypes
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings
from app.features.settings.defaults import DEFAULT_CR_SNOW_VISION_PROMPT
from app.features.settings.service import get_default_runtime_model_config, get_effective_api_key, get_model_runtime_configs, get_model_settings


@dataclass(frozen=True)
class VisionAnalysis:
    package_type: str | None
    keywords: list[str]
    brands: list[str]
    product_text: list[str]
    is_multi_product: bool
    primary_product_description: str
    raw_text: str
    source: str
    api_key_source: str
    model_profile: str = "default"
    model_calls: list[dict[str, Any]] | None = None


@dataclass(frozen=True)
class ModelTarget:
    name: str
    provider: str
    model: str
    endpoint: str
    api_key: str = ""
    api_key_source: str = ""


MODEL_FAILURE_SOURCES = {"model_error", "model_timeout", "qwen_error", "qwen_timeout", "no_api_key"}
PROVIDER_ENDPOINTS = {
    "aliyun": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    "volc": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
    "volcano": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
    "huoshan": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
}
TEST_IMAGE_DATA_URL = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAAAFElEQVR4nGP4TyJgGNUwqmH4agAAr639H708R/EAAAAASUVORK5CYII="
)


def empty_analysis(source: str = "fallback") -> VisionAnalysis:
    return VisionAnalysis(
        package_type=None,
        keywords=[],
        brands=[],
        product_text=[],
        is_multi_product=False,
        primary_product_description="",
        raw_text="",
        source=source,
        api_key_source="none",
        model_profile="default",
        model_calls=[],
    )


def analyze_product_image(
    image_path: Path,
    api_key_override: str | None = None,
    model_profile: str = "default",
) -> VisionAnalysis:
    model_settings = get_model_settings()
    model_config = get_default_runtime_model_config()
    effective_profile = str(model_config.get("id") or model_profile or "default") if model_config else str(model_profile or "default")
    plan = _resolve_node_model_plan(model_config, str(model_settings["vl_model"]), bool(model_settings.get("enable_vl_rerank", True)))
    timeout_seconds = int(model_settings.get("qwen_timeout_seconds", 10) or 10)
    vision_prompt = str(model_settings.get("vision_prompt", "") or "").strip() or DEFAULT_CR_SNOW_VISION_PROMPT
    mime_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
    data_url = f"data:{mime_type};base64,{base64.b64encode(image_path.read_bytes()).decode('utf-8')}"
    analyses: list[VisionAnalysis] = []
    model_calls: list[dict[str, Any]] = []
    for role, models in plan:
        role_analysis, role_calls = _call_role_with_fallback(
            role=role,
            models=models,
            data_url=data_url,
            api_key_override=api_key_override,
            model_settings=model_settings,
            timeout_seconds=timeout_seconds,
            vision_prompt=vision_prompt,
        model_profile=effective_profile,
        )
        model_calls.extend(role_calls)
        if role_analysis.source not in MODEL_FAILURE_SOURCES:
            analyses.append(role_analysis)
        else:
            return VisionAnalysis(**{**role_analysis.__dict__, "model_profile": effective_profile, "model_calls": model_calls})

    if not analyses:
        return VisionAnalysis(
            **{**empty_analysis("model_error").__dict__, "model_profile": effective_profile, "model_calls": model_calls}
        )
    if len(analyses) == 1:
        return VisionAnalysis(**{**analyses[0].__dict__, "model_profile": effective_profile, "model_calls": model_calls})
    merged = _merge_analyses(analyses)
    return VisionAnalysis(**{**merged.__dict__, "source": "model_multi", "model_profile": effective_profile, "model_calls": model_calls})


def _call_role_with_fallback(
    *,
    role: str,
    models: list[ModelTarget],
    data_url: str,
    api_key_override: str | None,
    model_settings: dict[str, object],
    timeout_seconds: int,
    vision_prompt: str,
    model_profile: str,
) -> tuple[VisionAnalysis, list[dict[str, Any]]]:
    calls: list[dict[str, Any]] = []
    last_analysis: VisionAnalysis | None = None
    for index, target in enumerate(models):
        if target.api_key:
            api_key, api_key_source = target.api_key, target.api_key_source or f"{target.name}:config"
        else:
            api_key, api_key_source = get_effective_api_key(api_key_override, provider=target.provider)
        started = time.perf_counter()
        if api_key:
            analysis = _call_qwen_model(
                role=role,
                target=target,
                data_url=data_url,
                api_key=api_key,
                api_key_source=api_key_source,
                timeout_seconds=timeout_seconds,
                vision_prompt=vision_prompt,
                model_profile=model_profile,
            )
        else:
            analysis = VisionAnalysis(
                **{
                    **empty_analysis("no_api_key").__dict__,
                    "api_key_source": f"{target.provider}:none",
                    "model_profile": model_profile,
                }
            )
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        calls.append(
            {
                "role": role,
                "provider": target.provider,
                "configName": target.name,
                "model": target.model,
                "attempt": index + 1,
                "source": analysis.source,
                "elapsedMs": elapsed_ms,
                "brands": analysis.brands[:8],
                "keywords": analysis.keywords[:12],
                "productText": analysis.product_text[:12],
                "rawText": analysis.raw_text[:500],
            }
        )
        last_analysis = analysis
        if analysis.source not in MODEL_FAILURE_SOURCES:
            return analysis, calls
    return last_analysis or empty_analysis("model_error"), calls


def _call_qwen_model(
    *,
    role: str,
    target: ModelTarget,
    data_url: str,
    api_key: str,
    api_key_source: str,
    timeout_seconds: int,
    vision_prompt: str,
    model_profile: str,
) -> VisionAnalysis:
    prompt = (
        "你是啤酒/饮料产品图片识别助手。请只输出 JSON，不要输出 Markdown。"
        "从图片中识别用于商品匹配的信息，字段包括："
        "package_type: 只能是 瓶、听、箱 或 null；"
        "brands: 可见品牌数组；keywords: 用于检索商品名称的关键词数组；"
        "product_text: 图片上能读到的商品文字数组；"
        "is_multi_product: 是否有多个商品；"
        "primary_product_description: 主体商品描述。"
        "只提取商品包装、瓶身、箱体上的品牌和文字；不要把巡检水印、拍照系统文字、手机时间、服务器时间、门店名称、地址当作商品文字或品牌。"
        "如果画面中只有边缘、角落、远处、很小或模糊的纸箱/瓶，不要强行猜品牌；brands 返回空数组，并在 primary_product_description 说明没有清晰商品主体。"
        "keywords 必须包含看得清的系列名、容量、度数、包装规格、瓶色/箱体特征，例如 500ml、8度、1*12、6*2、白瓶、绿瓶、纸箱。"
        "brands 必须提取最具体品牌或系列名，例如雪花纯生、勇闯天涯、SuperX、喜力、虎牌、红爵、AMSTEL、乌苏。"
        "如果看到雪花纯生、勇闯天涯、红爵、AMSTEL、8度、500ml、纸箱等文字，请务必提取。"
    )
    if role == "brand_package":
        prompt += "本轮重点识别品牌、系列、瓶/听/箱、主商品包装；对不确定文字少做猜测。"
    elif role == "ocr_text":
        prompt += "本轮重点识别包装上所有可见文字、容量、度数、规格、瓶色、箱体颜色和包装特征。"
    elif role == "final_judge":
        prompt += "本轮综合判断主体商品，不要被背景小商品、竞品或水印文字干扰。"
    prompt = f"{prompt}\n额外业务提示：{vision_prompt}"
    payload = {
        "model": target.model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        "temperature": 0,
    }
    request = Request(
        target.endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
    except TimeoutError:
        return VisionAnalysis(
            **{**empty_analysis("model_timeout").__dict__, "raw_text": "request timeout", "api_key_source": api_key_source, "model_profile": model_profile}
        )
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")[:800]
        return VisionAnalysis(
            **{**empty_analysis("model_error").__dict__, "raw_text": f"HTTP {exc.code}: {error_body}", "api_key_source": api_key_source, "model_profile": model_profile}
        )
    except URLError as exc:
        if isinstance(exc.reason, TimeoutError):
            return VisionAnalysis(
                **{**empty_analysis("model_timeout").__dict__, "raw_text": "request timeout", "api_key_source": api_key_source, "model_profile": model_profile}
            )
        return VisionAnalysis(
            **{**empty_analysis("model_error").__dict__, "raw_text": str(exc.reason)[:800], "api_key_source": api_key_source, "model_profile": model_profile}
        )
    except json.JSONDecodeError:
        return VisionAnalysis(
            **{**empty_analysis("model_error").__dict__, "raw_text": "response is not valid JSON", "api_key_source": api_key_source, "model_profile": model_profile}
        )

    content = str(body.get("choices", [{}])[0].get("message", {}).get("content", ""))
    parsed = _parse_json_content(content)
    return VisionAnalysis(
        package_type=_clean_package_type(parsed.get("package_type")),
        keywords=_as_str_list(parsed.get("keywords")),
        brands=_as_str_list(parsed.get("brands")),
        product_text=_as_str_list(parsed.get("product_text")),
        is_multi_product=bool(parsed.get("is_multi_product", False)),
        primary_product_description=str(parsed.get("primary_product_description") or ""),
        raw_text=content,
        source=target.provider,
        api_key_source=api_key_source,
        model_profile=model_profile,
        model_calls=[],
    )


def test_model_connection(
    *,
    provider: str,
    model: str,
    config_id: str = "",
    config_name: str = "",
    base_url: str = "",
    api_key_override: str | None = None,
    timeout_seconds: int = 10,
) -> dict[str, object]:
    runtime_configs = get_model_runtime_configs()
    config = _find_model_config(config_id, runtime_configs) or _find_model_config(config_name, runtime_configs)
    if config:
        target = ModelTarget(
            name=str(config.get("name") or config_name or model),
            provider=_normalize_provider(provider or str(config.get("provider", "aliyun"))),
            model=model,
            endpoint=base_url or str(config.get("base_url") or PROVIDER_ENDPOINTS.get(_normalize_provider(provider), PROVIDER_ENDPOINTS["aliyun"])),
            api_key=str(config.get("api_key") or ""),
            api_key_source=f"{config.get('name') or config_name or model}:config",
        )
    else:
        normalized_provider = _normalize_provider(provider)
        target = ModelTarget(
            name=config_name or model,
            provider=normalized_provider,
            model=model,
            endpoint=base_url or PROVIDER_ENDPOINTS.get(normalized_provider, PROVIDER_ENDPOINTS["aliyun"]),
        )
    if api_key_override and api_key_override.strip():
        api_key, api_key_source = api_key_override.strip(), f"{target.provider}:request"
    elif target.api_key:
        api_key, api_key_source = target.api_key, target.api_key_source or f"{target.name}:config"
    else:
        api_key, api_key_source = get_effective_api_key(None, provider=target.provider)
    if not api_key:
        return {
            "ok": False,
            "provider": target.provider,
            "configName": target.name,
            "model": target.model,
            "endpoint": target.endpoint,
            "apiKeySource": api_key_source,
            "elapsedMs": 0,
            "message": "未配置该平台 API Key",
        }

    payload = {
        "model": target.model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": TEST_IMAGE_DATA_URL}},
                    {"type": "text", "text": "请识别这张测试图片并只返回 JSON：{\"ok\":true,\"message\":\"vision_model_test_ok\"}"},
                ],
            }
        ],
        "temperature": 0,
    }
    request = Request(
        target.endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        content = str(body.get("choices", [{}])[0].get("message", {}).get("content", ""))
        return {
            "ok": True,
            "provider": target.provider,
            "configName": target.name,
            "model": target.model,
            "endpoint": target.endpoint,
            "apiKeySource": api_key_source,
            "elapsedMs": elapsed_ms,
            "message": content[:500],
        }
    except TimeoutError:
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        return {
            "ok": False,
            "provider": target.provider,
            "configName": target.name,
            "model": target.model,
            "endpoint": target.endpoint,
            "apiKeySource": api_key_source,
            "elapsedMs": elapsed_ms,
            "message": "模型测试超时",
        }
    except HTTPError as exc:
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        error_body = exc.read().decode("utf-8", errors="replace")[:800]
        return {
            "ok": False,
            "provider": target.provider,
            "configName": target.name,
            "model": target.model,
            "endpoint": target.endpoint,
            "apiKeySource": api_key_source,
            "elapsedMs": elapsed_ms,
            "message": _format_provider_http_error(target.provider, exc.code, error_body),
        }
    except URLError as exc:
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        return {
            "ok": False,
            "provider": target.provider,
            "configName": target.name,
            "model": target.model,
            "endpoint": target.endpoint,
            "apiKeySource": api_key_source,
            "elapsedMs": elapsed_ms,
            "message": str(exc.reason)[:800],
        }
    except json.JSONDecodeError:
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        return {
            "ok": False,
            "provider": target.provider,
            "model": target.model,
            "endpoint": target.endpoint,
            "apiKeySource": api_key_source,
            "elapsedMs": elapsed_ms,
            "message": "响应不是合法 JSON",
        }


def _resolve_effective_model_profile(*, model_profile: str, task_model_profile: str, model_profiles: str) -> str:
    requested = (model_profile or "default").strip() or "default"
    if requested == "default":
        selected = (task_model_profile or "default").strip() or "default"
    else:
        selected = requested
    profile_map = _parse_model_profiles(model_profiles)
    seen: set[str] = set()
    while selected in profile_map and selected not in seen:
        seen.add(selected)
        selected = profile_map[selected].strip() or "default"
    return selected


def _parse_model_profiles(value: str) -> dict[str, str]:
    profiles: dict[str, str] = {}
    for raw_line in str(value or "").replace("；", "\n").replace(";", "\n").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            name, profile = line.split("=", 1)
        elif ":" in line and not line.startswith("high_accuracy:"):
            name, profile = line.split(":", 1)
        else:
            continue
        name = name.strip()
        profile = profile.strip()
        if name and profile:
            profiles[name] = profile
    return profiles


def _resolve_node_model_plan(
    model_config: dict[str, object] | None,
    default_model: str,
    enable_multi_node: bool,
) -> list[tuple[str, list[ModelTarget]]]:
    if not model_config:
        return [("default", [ModelTarget(name=default_model, provider="aliyun", model=default_model, endpoint=PROVIDER_ENDPOINTS["aliyun"])])]
    provider = _normalize_provider(str(model_config.get("provider", "aliyun") or "aliyun"))
    endpoint = str(model_config.get("base_url") or PROVIDER_ENDPOINTS.get(provider, PROVIDER_ENDPOINTS["aliyun"])).strip()
    config_name = str(model_config.get("name") or model_config.get("id") or provider)
    node_models = model_config.get("node_models") if isinstance(model_config.get("node_models"), dict) else {}
    fallback_model = str(model_config.get("model") or default_model).strip()

    def target(role: str) -> ModelTarget:
        model = str(node_models.get(role) or fallback_model).strip() if isinstance(node_models, dict) else fallback_model
        return ModelTarget(
            name=f"{config_name}:{role}",
            provider=provider,
            model=model,
            endpoint=endpoint,
            api_key=str(model_config.get("api_key") or "").strip(),
            api_key_source=f"{config_name}:config",
        )

    if not enable_multi_node:
        return [("default", [target("default")])]
    return [
        ("brand_package", [target("brand_package")]),
        ("ocr_text", [target("ocr_text")]),
        ("final_judge", [target("final_judge")]),
    ]


def _resolve_model_plan(
    model_profile: str,
    default_model: str,
    default_provider: str,
    model_configs: list[dict[str, object]] | None = None,
) -> list[tuple[str, list[ModelTarget]]]:
    profile = (model_profile or "default").strip()
    if profile in {"", "default"}:
        return [("default", [_parse_model_target(default_model, default_provider, model_configs)])]
    if profile in {"high_accuracy", "multi_model", "multi"}:
        return [
            ("brand_package", [_parse_model_target(default_model, default_provider, model_configs)]),
            ("ocr_text", [_parse_model_target(default_model, default_provider, model_configs)]),
            ("final_judge", [_parse_model_target(default_model, default_provider, model_configs)]),
        ]
    if profile.startswith("high_accuracy:"):
        models = [item.strip() for item in profile.split(":", 1)[1].split(",") if item.strip()]
        while len(models) < 3:
            models.append(models[-1] if models else default_model)
        return [
            ("brand_package", [_parse_model_target(models[0], default_provider, model_configs)]),
            ("ocr_text", [_parse_model_target(models[1], default_provider, model_configs)]),
            ("final_judge", [_parse_model_target(models[2], default_provider, model_configs)]),
        ]
    if "," in profile:
        models = [item.strip() for item in profile.split(",") if item.strip()]
        while len(models) < 3:
            models.append(models[-1] if models else default_model)
        return [
            ("brand_package", [_parse_model_target(models[0], default_provider, model_configs)]),
            ("ocr_text", [_parse_model_target(models[1], default_provider, model_configs)]),
            ("final_judge", [_parse_model_target(models[2], default_provider, model_configs)]),
        ]
    fallback_models = [item.strip() for item in profile.split("|") if item.strip()] or [default_model]
    return [("default", [_parse_model_target(item, default_provider, model_configs) for item in fallback_models])]


def _parse_model_target(
    value: str,
    default_provider: str,
    model_configs: list[dict[str, object]] | None = None,
) -> ModelTarget:
    text = str(value or "").strip()
    config = _find_model_config(text, model_configs or [])
    if config:
        provider = _normalize_provider(str(config.get("provider", default_provider) or default_provider))
        return ModelTarget(
            name=str(config.get("name") or text),
            provider=provider,
            model=str(config.get("model") or text).strip(),
            endpoint=str(config.get("base_url") or PROVIDER_ENDPOINTS.get(provider, PROVIDER_ENDPOINTS["aliyun"])).strip(),
            api_key=str(config.get("api_key") or "").strip(),
            api_key_source=f"{config.get('name') or text}:config",
        )
    provider = (default_provider or "aliyun").strip().lower()
    model = text
    endpoint = ""
    if "::" in text:
        provider, model = text.split("::", 1)
    elif ":" in text:
        prefix, rest = text.split(":", 1)
        if prefix.strip().lower() in PROVIDER_ENDPOINTS or prefix.strip().lower() in {"aliyun", "volc"}:
            provider, model = prefix, rest
    elif "/" in text:
        prefix, rest = text.split("/", 1)
        if prefix.strip().lower() in PROVIDER_ENDPOINTS or prefix.strip().lower() in {"aliyun", "volc"}:
            provider, model = prefix, rest
    provider = _normalize_provider(provider)
    endpoint = PROVIDER_ENDPOINTS.get(provider, PROVIDER_ENDPOINTS["aliyun"])
    return ModelTarget(name=model.strip(), provider=provider, model=model.strip(), endpoint=endpoint)


def _find_model_config(value: str, configs: list[dict[str, object]]) -> dict[str, object] | None:
    key = str(value or "").strip()
    if not key:
        return None
    for item in configs:
        if not bool(item.get("enabled", True)):
            continue
        names = {str(item.get("id") or "").strip(), str(item.get("name") or "").strip()}
        if key in names:
            return item
    return None


def _format_provider_http_error(provider: str, status_code: int, error_body: str) -> str:
    message = f"HTTP {status_code}: {error_body}"
    if _normalize_provider(provider) == "volc" and status_code == 404 and "InvalidEndpointOrModel.NotFound" in error_body:
        message += (
            "\n\n火山 Ark 提示：model 字段需要填写可调用的 Model ID 或 Endpoint ID。"
            "不要填写展示名，例如 Doubao-Seed-2.0-Pro。"
            "可尝试填写控制台中的 ep-... 接入点，或已开通的模型 ID，"
            "例如 doubao-seed-2-0-pro-260215 / doubao-seed-2-1-pro-260628。"
        )
    return message


def _normalize_provider(provider: str) -> str:
    text = str(provider or "aliyun").strip().lower()
    if text in {"dashscope", "ali", "aliyun", "qwen"}:
        return "aliyun"
    if text in {"volc", "volcano", "huoshan", "ark", "doubao"}:
        return "volc"
    return text


def _merge_analyses(analyses: list[VisionAnalysis]) -> VisionAnalysis:
    return VisionAnalysis(
        package_type=next((item.package_type for item in analyses if item.package_type), None),
        keywords=_unique_text([keyword for item in analyses for keyword in item.keywords]),
        brands=_unique_text([brand for item in analyses for brand in item.brands]),
        product_text=_unique_text([text for item in analyses for text in item.product_text]),
        is_multi_product=any(item.is_multi_product for item in analyses),
        primary_product_description="；".join(item.primary_product_description for item in analyses if item.primary_product_description),
        raw_text="\n".join(item.raw_text for item in analyses if item.raw_text),
        source="qwen_multi",
        api_key_source=analyses[0].api_key_source,
        model_profile=analyses[0].model_profile,
        model_calls=[],
    )


def _unique_text(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        key = text.lower().replace(" ", "")
        if text and key not in seen:
            seen.add(key)
            result.append(text)
    return result


def _parse_json_content(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end >= start:
        text = text[start : end + 1]
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _clean_package_type(value: Any) -> str | None:
    text = str(value or "").strip()
    for candidate in ["瓶", "听", "箱"]:
        if candidate in text:
            return candidate
    return None
