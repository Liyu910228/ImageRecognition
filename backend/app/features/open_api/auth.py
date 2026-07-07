from __future__ import annotations

import secrets
from datetime import datetime, timezone

from fastapi import Header, HTTPException

from app.core.config import settings
from app.features.settings.repository import load_json_settings, save_json_settings


def verify_open_api_key(authorization: str | None = Header(default=None)) -> str:
    token = _extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="缺少开放接口 Authorization Bearer Token")
    if not any(secrets.compare_digest(token, item["key"]) for item in list_open_api_keys() if item.get("enabled", True)):
        raise HTTPException(status_code=403, detail="开放接口 Token 无效或已停用")
    return token


def list_open_api_keys() -> list[dict[str, object]]:
    env_keys = [
        {"name": "env", "key": item.strip(), "enabled": True, "source": "env"}
        for item in settings.open_api_keys.replace("\n", ",").split(",")
        if item.strip()
    ]
    stored = load_json_settings(settings.open_api_keys_path) or {}
    stored_keys = stored.get("keys") if isinstance(stored.get("keys"), list) else []
    return [*env_keys, *[item for item in stored_keys if isinstance(item, dict)]]


def ensure_default_open_api_key() -> dict[str, object]:
    keys = list_open_api_keys()
    if keys:
        first = keys[0]
        return {
            "configured": True,
            "name": first.get("name", "default"),
            "key": first.get("key", ""),
            "source": first.get("source", "runtime"),
        }

    generated_key = f"crsnow_{secrets.token_urlsafe(24)}"
    payload = {
        "keys": [
            {
                "name": "default",
                "key": generated_key,
                "enabled": True,
                "source": "runtime",
                "createdAt": datetime.now(timezone.utc).isoformat(),
            }
        ]
    }
    save_json_settings(settings.open_api_keys_path, payload)
    return {"configured": True, "name": "default", "key": generated_key, "source": "runtime"}


def rotate_default_open_api_key(name: str = "default") -> dict[str, object]:
    generated_key = f"crsnow_{secrets.token_urlsafe(24)}"
    payload = {
        "keys": [
            {
                "name": name.strip() or "default",
                "key": generated_key,
                "enabled": True,
                "source": "runtime",
                "createdAt": datetime.now(timezone.utc).isoformat(),
            }
        ]
    }
    save_json_settings(settings.open_api_keys_path, payload)
    return {
        "configured": True,
        "name": payload["keys"][0]["name"],
        "key": generated_key,
        "source": "runtime",
        "maskedKey": _mask_key(generated_key),
    }


def public_open_api_status() -> dict[str, object]:
    keys = list_open_api_keys()
    return {
        "configured": bool(keys),
        "keys": [
            {
                "name": str(item.get("name", "")),
                "enabled": bool(item.get("enabled", True)),
                "source": str(item.get("source", "runtime")),
                "maskedKey": _mask_key(str(item.get("key", ""))),
            }
            for item in keys
        ],
    }


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        return ""
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        return ""
    return token.strip()


def _mask_key(value: str) -> str:
    if len(value) <= 10:
        return "***"
    return f"{value[:6]}...{value[-4:]}"
