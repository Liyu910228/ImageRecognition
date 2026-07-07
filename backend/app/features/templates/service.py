from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.core.config import settings
from app.features.templates.extractor import extract_workbooks
from app.features.templates.indexer import build_feature_index
from app.features.templates.repository import get_template_status, list_template_sources


def normalize_upload_filename(filename: str) -> str:
    try:
        return filename.encode("latin1").decode("utf-8")
    except UnicodeError:
        return filename


async def upload_template_workbooks(files: list[UploadFile]) -> dict[str, object]:
    if not files:
        raise HTTPException(status_code=400, detail="请至少上传一个 Excel 模板文件")

    settings.template_sources_dir.mkdir(parents=True, exist_ok=True)
    workbook_paths: list[Path] = []

    for file in files:
        filename = normalize_upload_filename(file.filename or "")
        if Path(filename).suffix.lower() != ".xlsx":
            raise HTTPException(status_code=400, detail="模板库仅支持 .xlsx 文件")
        target = settings.template_sources_dir / Path(filename).name
        with target.open("wb") as output:
            shutil.copyfileobj(file.file, output)
        workbook_paths.append(target)

    return rebuild_templates([path.name for path in workbook_paths])


def rebuild_templates(uploaded_files: list[str] | None = None) -> dict[str, object]:
    workbook_paths = sorted(settings.template_sources_dir.glob("*.xlsx"))
    if not workbook_paths:
        raise HTTPException(status_code=409, detail="没有可构建的模板库源文件")

    records = extract_workbooks(workbook_paths, settings.product_templates_dir)
    indexed_count = build_feature_index(settings.template_manifest_path, settings.vector_index_path)
    status = get_template_status(settings.template_manifest_path, settings.vector_index_path)
    sources = list_template_sources(settings.template_sources_dir)

    return {
        "uploadedFiles": uploaded_files or [],
        "productCount": len(records),
        "indexedImageCount": indexed_count,
        "sources": sources,
        "status": status,
    }


def get_template_sources() -> dict[str, object]:
    return {
        "sources": list_template_sources(settings.template_sources_dir),
        "status": get_template_status(settings.template_manifest_path, settings.vector_index_path),
    }


def delete_template_source(filename: str) -> dict[str, object]:
    if Path(filename).name != filename or Path(filename).suffix.lower() != ".xlsx":
        raise HTTPException(status_code=400, detail="模板文件名不合法")

    target = settings.template_sources_dir / filename
    if not target.exists():
        raise HTTPException(status_code=404, detail="模板源文件不存在")
    target.unlink()

    remaining = list(settings.template_sources_dir.glob("*.xlsx"))
    if not remaining:
        if settings.product_templates_dir.exists():
            shutil.rmtree(settings.product_templates_dir)
        settings.product_templates_dir.mkdir(parents=True, exist_ok=True)
        return {
            "deletedFile": filename,
            "productCount": 0,
            "indexedImageCount": 0,
            "sources": [],
            "status": get_template_status(settings.template_manifest_path, settings.vector_index_path),
        }

    result = rebuild_templates()
    return {"deletedFile": filename, **result}


def download_template_source(filename: str) -> Path:
    if Path(filename).name != filename or Path(filename).suffix.lower() != ".xlsx":
        raise HTTPException(status_code=400, detail="模板文件名不合法")

    target = settings.template_sources_dir / filename
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="模板源文件不存在")
    return target
