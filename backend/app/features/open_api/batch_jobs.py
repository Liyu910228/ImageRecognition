from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.features.recognition.service import recognize_image_url


_JOB_LOCK = threading.Lock()


def mark_interrupted_jobs() -> None:
    root = settings.open_batch_jobs_dir
    if not root.exists():
        return
    for job_path in root.glob("*/job.json"):
        try:
            job = json.loads(job_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if job.get("status") in {"pending", "running"}:
            job["status"] = "interrupted"
            job["error"] = "服务重启，任务已中断，请重新提交。"
            job["updated_at"] = _now()
            job_path.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")


def create_batch_job(
    *,
    items: list[dict[str, str]],
    hints: str = "",
    model_profile: str = "default",
    callback_url: str = "",
) -> dict[str, object]:
    if not items:
        raise ValueError("批量任务至少需要一条图片链接")
    job_id = f"JOB{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"
    job_dir = _job_dir(job_id)
    job_dir.mkdir(parents=True, exist_ok=False)
    now = _now()
    normalized_items = []
    for index, item in enumerate(items, start=1):
        trace_id = str(item.get("trace_id") or "").strip() or f"{job_id}-{index:06d}"
        normalized_items.append(
            {
                "index": index,
                "trace_id": trace_id,
                "image_url": str(item.get("image_url") or "").strip(),
            }
        )
    _write_jsonl(job_dir / "sources.jsonl", normalized_items)
    job = {
        "job_id": job_id,
        "status": "pending",
        "total": len(normalized_items),
        "processed": 0,
        "success": 0,
        "no_match": 0,
        "failed": 0,
        "hints": hints,
        "model_profile": model_profile,
        "callback_url": callback_url,
        "created_at": now,
        "updated_at": now,
        "started_at": "",
        "completed_at": "",
        "error": "",
    }
    _save_job(job)
    thread = threading.Thread(target=_run_batch_job, args=(job_id,), daemon=True)
    thread.start()
    return _public_job(job)


def get_batch_job(job_id: str) -> dict[str, object]:
    return _public_job(_load_job(job_id))


def list_batch_job_items(
    *,
    job_id: str,
    page: int = 1,
    page_size: int = 100,
    status: str = "all",
    query: str = "",
) -> dict[str, object]:
    _load_job(job_id)
    results = _read_jsonl(_job_dir(job_id) / "results.jsonl")
    filtered = [
        item
        for item in results
        if _matches_item_filter(item, status=status, query=query)
    ]
    current_page = max(page, 1)
    limit = max(min(page_size, 500), 1)
    start = (current_page - 1) * limit
    end = start + limit
    return {
        "job_id": job_id,
        "items": filtered[start:end],
        "total": len(filtered),
        "page": current_page,
        "pageSize": limit,
    }


def _run_batch_job(job_id: str) -> None:
    job = _load_job(job_id)
    job["status"] = "running"
    job["started_at"] = job.get("started_at") or _now()
    job["updated_at"] = _now()
    _save_job(job)
    sources = _read_jsonl(_job_dir(job_id) / "sources.jsonl")
    try:
        for source in sources:
            item_result = _process_batch_item(job, source)
            _append_jsonl(_job_dir(job_id) / "results.jsonl", item_result)
            _update_job_counts(job_id, item_result["status"])
        job = _load_job(job_id)
        job["status"] = "completed"
        job["completed_at"] = _now()
        job["updated_at"] = job["completed_at"]
        _save_job(job)
    except Exception as exc:  # noqa: BLE001
        job = _load_job(job_id)
        job["status"] = "failed"
        job["error"] = str(exc)
        job["updated_at"] = _now()
        _save_job(job)


def _process_batch_item(job: dict[str, Any], source: dict[str, Any]) -> dict[str, object]:
    trace_id = str(source.get("trace_id") or "")
    image_url = str(source.get("image_url") or "")
    try:
        result = recognize_image_url(
            image_url,
            hints=str(job.get("hints") or ""),
            trace_id=trace_id,
            model_profile=str(job.get("model_profile") or "default"),
        )
        best = result.get("best") if isinstance(result.get("best"), dict) else None
        analysis = result.get("analysis") if isinstance(result.get("analysis"), dict) else {}
        status = "命中" if best else "未命中"
        return {
            "index": source.get("index"),
            "trace_id": result.get("traceId") or trace_id,
            "image_url": image_url,
            "status": status,
            "product_code": best.get("product_code", "") if best else "",
            "product_name": best.get("product_name", "") if best else "",
            "package_type": best.get("package_type", "") if best else "",
            "score": best.get("score") if best else None,
            "template_image_url": best.get("template_image_url") if best else None,
            "matched_snow_brands": analysis.get("matchedSnowBrands", []),
            "matched_competitor_brands": analysis.get("matchedCompetitorBrands", []),
            "review_required": bool(result.get("reviewRequired", False)),
            "model_profile": job.get("model_profile", "default"),
            "model_calls": analysis.get("modelCalls", []),
            "error": "",
            "created_at": _now(),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "index": source.get("index"),
            "trace_id": trace_id,
            "image_url": image_url,
            "status": "失败",
            "product_code": "",
            "product_name": "",
            "package_type": "",
            "score": None,
            "template_image_url": None,
            "matched_snow_brands": [],
            "matched_competitor_brands": [],
            "review_required": False,
            "model_profile": job.get("model_profile", "default"),
            "model_calls": [],
            "error": str(exc),
            "created_at": _now(),
        }


def _update_job_counts(job_id: str, item_status: str) -> None:
    with _JOB_LOCK:
        job = _load_job(job_id)
        job["processed"] = int(job.get("processed") or 0) + 1
        if item_status == "命中":
            job["success"] = int(job.get("success") or 0) + 1
        elif item_status == "未命中":
            job["no_match"] = int(job.get("no_match") or 0) + 1
        else:
            job["failed"] = int(job.get("failed") or 0) + 1
        job["updated_at"] = _now()
        _save_job(job)


def _matches_item_filter(item: dict[str, Any], *, status: str, query: str) -> bool:
    if status != "all" and str(item.get("status", "")) != status:
        return False
    keyword = query.strip().lower()
    if not keyword:
        return True
    return keyword in json.dumps(item, ensure_ascii=False).lower()


def _public_job(job: dict[str, Any]) -> dict[str, object]:
    total = int(job.get("total") or 0)
    processed = int(job.get("processed") or 0)
    return {
        "job_id": job.get("job_id", ""),
        "status": job.get("status", ""),
        "total": total,
        "processed": processed,
        "success": int(job.get("success") or 0),
        "no_match": int(job.get("no_match") or 0),
        "failed": int(job.get("failed") or 0),
        "progress": round(processed / total, 6) if total else 0,
        "model_profile": job.get("model_profile", "default"),
        "created_at": job.get("created_at", ""),
        "updated_at": job.get("updated_at", ""),
        "started_at": job.get("started_at", ""),
        "completed_at": job.get("completed_at", ""),
        "error": job.get("error", ""),
    }


def _job_dir(job_id: str) -> Path:
    safe_job_id = "".join(char for char in job_id if char.isalnum() or char in {"-", "_"})
    return settings.open_batch_jobs_dir / safe_job_id


def _load_job(job_id: str) -> dict[str, Any]:
    path = _job_dir(job_id) / "job.json"
    if not path.exists():
        raise FileNotFoundError("批量任务不存在")
    return json.loads(path.read_text(encoding="utf-8"))


def _save_job(job: dict[str, Any]) -> None:
    job_dir = _job_dir(str(job["job_id"]))
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "job.json").write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, items: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in items:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")


def _append_jsonl(path: Path, item: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            items.append(parsed)
    return items


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
