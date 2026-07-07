from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, HttpUrl

from app.features.open_api.auth import public_open_api_status, rotate_default_open_api_key, verify_open_api_key
from app.features.open_api.batch_jobs import create_batch_job, get_batch_job, list_batch_job_items
from app.features.recognition.service import extract_image_links_from_workbook, recognize_image_url


class OpenRecognitionRequest(BaseModel):
    image_url: HttpUrl
    trace_id: str = ""
    hints: str = ""
    model_profile: str = "default"
    callback_url: HttpUrl | None = None


class OpenApiTokenRequest(BaseModel):
    name: str = "default"


class OpenBatchImage(BaseModel):
    image_url: HttpUrl
    trace_id: str = ""


class OpenBatchJobRequest(BaseModel):
    items: list[OpenBatchImage] = []
    image_urls: list[HttpUrl] = []
    hints: str = ""
    model_profile: str = "default"
    callback_url: HttpUrl | None = None


router = APIRouter()


@router.get("/open/status")
def open_api_status() -> dict[str, object]:
    return public_open_api_status()


@router.post("/open/tokens")
def generate_open_api_token(payload: OpenApiTokenRequest) -> dict[str, object]:
    return rotate_default_open_api_key(payload.name)


@router.post("/open/recognitions")
def create_open_recognition(
    payload: OpenRecognitionRequest,
    _: str = Depends(verify_open_api_key),
) -> dict[str, object]:
    result = recognize_image_url(
        str(payload.image_url),
        hints=payload.hints,
        trace_id=payload.trace_id,
        model_profile=payload.model_profile,
    )
    best = result.get("best") if isinstance(result.get("best"), dict) else None
    analysis = result.get("analysis") if isinstance(result.get("analysis"), dict) else {}
    return {
        "trace_id": result.get("traceId") or payload.trace_id,
        "status": "命中" if best else "未命中",
        "product_code": best.get("product_code", "") if best else "",
        "product_name": best.get("product_name", "") if best else "",
        "package_type": best.get("package_type", "") if best else "",
        "score": best.get("score") if best else None,
        "template_image_url": best.get("template_image_url") if best else None,
        "matched_snow_brands": analysis.get("matchedSnowBrands", []),
        "matched_competitor_brands": analysis.get("matchedCompetitorBrands", []),
        "review_required": bool(result.get("reviewRequired", False)),
        "model_profile": payload.model_profile,
        "model_calls": analysis.get("modelCalls", []),
        "raw": result,
    }


@router.post("/open/batch-jobs")
def create_open_batch_job(
    payload: OpenBatchJobRequest,
    _: str = Depends(verify_open_api_key),
) -> dict[str, object]:
    items = [
        {"image_url": str(item.image_url), "trace_id": item.trace_id}
        for item in payload.items
    ]
    items.extend({"image_url": str(image_url), "trace_id": ""} for image_url in payload.image_urls)
    try:
        return create_batch_job(
            items=items,
            hints=payload.hints,
            model_profile=payload.model_profile,
            callback_url=str(payload.callback_url or ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/open/batch-jobs/workbook")
def create_open_batch_job_from_workbook(
    file: UploadFile = File(...),
    hints: str = Form(default=""),
    model_profile: str = Form(default="default"),
    callback_url: str = Form(default=""),
    _: str = Depends(verify_open_api_key),
) -> dict[str, object]:
    workbook_payload = extract_image_links_from_workbook(file)
    links = workbook_payload.get("links") if isinstance(workbook_payload.get("links"), list) else []
    items = [
        {
            "image_url": str(item.get("image_url", "")),
            "trace_id": f"{item.get('sheet', 'Sheet')}-第{item.get('row', '')}行",
        }
        for item in links
        if isinstance(item, dict)
    ]
    try:
        job = create_batch_job(
            items=items,
            hints=hints,
            model_profile=model_profile,
            callback_url=callback_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        **job,
        "source_filename": workbook_payload.get("filename", file.filename or ""),
        "source_field": workbook_payload.get("field", "照片链接"),
    }


@router.get("/open/batch-jobs/{job_id}")
def get_open_batch_job(
    job_id: str,
    _: str = Depends(verify_open_api_key),
) -> dict[str, object]:
    try:
        return get_batch_job(job_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="批量任务不存在") from exc


@router.get("/open/batch-jobs/{job_id}/items")
def list_open_batch_job_items(
    job_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500, alias="pageSize"),
    status: str = Query(default="all"),
    q: str = Query(default=""),
    _: str = Depends(verify_open_api_key),
) -> dict[str, object]:
    try:
        return list_batch_job_items(job_id=job_id, page=page, page_size=page_size, status=status, query=q)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="批量任务不存在") from exc
