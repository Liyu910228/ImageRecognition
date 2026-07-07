from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings


def append_recognition_log(event: dict[str, Any]) -> None:
    settings.recognition_log_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    payload = {
        "id": now.strftime("%Y%m%d%H%M%S%f"),
        "createdAt": now.isoformat(),
        **event,
    }
    with settings.recognition_log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_recognition_logs(
    limit: int = 50,
    page: int = 1,
    query: str = "",
    status: str = "all",
    snow_gate: str = "all",
    competitor: str = "all",
    selected_ids: set[str] | None = None,
) -> dict[str, Any]:
    parsed_lines = _read_all_logs()
    filtered_lines = [
        item
        for item in parsed_lines
        if _matches_filters(
            item,
            query=query,
            status=status,
            snow_gate=snow_gate,
            competitor=competitor,
            selected_ids=selected_ids,
        )
    ]
    total = len(filtered_lines)
    page_size = max(limit, 1)
    current_page = max(page, 1)
    start = (current_page - 1) * page_size
    end = start + page_size
    page_items = list(reversed(filtered_lines))[start:end]
    result: list[dict[str, Any]] = []
    for offset, parsed in enumerate(page_items):
        parsed["sequence"] = start + offset + 1
        result.append(parsed)
    return {"items": result, "total": total, "page": current_page, "pageSize": page_size}


def clear_recognition_logs() -> None:
    path = settings.recognition_log_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def _read_all_logs() -> list[dict[str, Any]]:
    path = settings.recognition_log_path
    if not path.exists():
        return []
    parsed_lines: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            parsed_lines.append(parsed)
    return parsed_lines


def _matches_filters(
    item: dict[str, Any],
    *,
    query: str,
    status: str,
    snow_gate: str,
    competitor: str,
    selected_ids: set[str] | None,
) -> bool:
    if selected_ids is not None and str(item.get("id", "")) not in selected_ids:
        return False
    if status != "all" and _normalize_status(str(item.get("status", ""))) != _normalize_status(status):
        return False

    gate = item.get("gate") if isinstance(item.get("gate"), dict) else {}
    if snow_gate == "pass" and not bool(gate.get("hasSnowBrand")):
        return False
    if snow_gate == "fail" and bool(gate.get("hasSnowBrand")):
        return False
    if competitor == "yes" and not bool(gate.get("hasCompetitorBrand")):
        return False
    if competitor == "no" and bool(gate.get("hasCompetitorBrand")):
        return False

    keyword = query.strip().lower()
    if not keyword:
        return True
    return keyword in _flatten_for_search(item).lower()


def _flatten_for_search(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_flatten_for_search(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_flatten_for_search(item) for item in value)
    return str(value or "")


def _normalize_status(value: str) -> str:
    if value in {"命中", "鍛戒腑"}:
        return "hit"
    if value in {"未命中", "鏈懡涓?"} or value.startswith("鏈"):
        return "miss"
    return value
