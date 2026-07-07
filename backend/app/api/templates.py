from fastapi import APIRouter, File, UploadFile
from fastapi.responses import FileResponse

from app.features.templates.service import (
    delete_template_source,
    download_template_source,
    get_template_sources,
    upload_template_workbooks,
)


router = APIRouter()


@router.post("/templates/upload")
async def upload_templates(files: list[UploadFile] = File(...)) -> dict[str, object]:
    return await upload_template_workbooks(files)


@router.get("/templates/sources")
def list_template_files() -> dict[str, object]:
    return get_template_sources()


@router.delete("/templates/sources/{filename}")
def delete_template_file(filename: str) -> dict[str, object]:
    return delete_template_source(filename)


@router.get("/templates/sources/{filename}/download")
def download_template_file(filename: str) -> FileResponse:
    path = download_template_source(filename)
    return FileResponse(
        path=path,
        filename=path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
