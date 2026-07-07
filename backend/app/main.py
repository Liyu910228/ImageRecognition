from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import health, logs, open_api, recognition, settings as settings_api, status, templates
from app.core.config import PROJECT_ROOT, settings
from app.features.open_api.batch_jobs import mark_interrupted_jobs


FRONTEND_DIST_DIR = PROJECT_ROOT / "frontend/dist"


def create_app() -> FastAPI:
    app = FastAPI(title="Product Image Recognition API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(status.router, prefix="/api", tags=["status"])
    app.include_router(recognition.router, prefix="/api", tags=["recognition"])
    app.include_router(open_api.router, prefix="/api", tags=["open-api"])
    app.include_router(logs.router, prefix="/api", tags=["logs"])
    app.include_router(settings_api.router, prefix="/api", tags=["settings"])
    app.include_router(templates.router, prefix="/api", tags=["templates"])
    mark_interrupted_jobs()
    settings.template_images_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/template-images", StaticFiles(directory=settings.template_images_dir), name="template-images")
    if FRONTEND_DIST_DIR.exists():
        app.mount("/", StaticFiles(directory=FRONTEND_DIST_DIR, html=True), name="frontend")
    return app


app = create_app()
