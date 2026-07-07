from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    dashscope_api_key: str = ""
    qwen_embedding_model: str = "qwen3-vl-embedding"
    qwen_vl_model: str = "qwen3-vl-plus"
    upload_max_mb: int = 10
    worker_concurrency: int = 1
    admin_token: str = ""
    open_api_keys: str = ""
    data_dir: Path = PROJECT_ROOT / "backend/data"
    template_sources_dir: Path = PROJECT_ROOT / "backend/data/template_sources"
    product_templates_dir: Path = PROJECT_ROOT / "outputs/product_templates"
    template_manifest_path: Path = PROJECT_ROOT / "outputs/product_templates/manifest.json"
    vector_index_path: Path = PROJECT_ROOT / "outputs/product_templates/feature_index.json"
    template_images_dir: Path = PROJECT_ROOT / "outputs/product_templates/images"
    low_confidence_threshold: float = 0.72
    model_settings_path: Path = PROJECT_ROOT / "backend/data/model_settings.json"
    open_api_keys_path: Path = PROJECT_ROOT / "backend/data/open_api_keys.json"
    open_batch_jobs_dir: Path = PROJECT_ROOT / "backend/data/open_batch_jobs"
    recognition_log_path: Path = PROJECT_ROOT / "backend/data/recognition_logs.jsonl"
    cors_origins: list[str] = ["http://localhost:8080", "http://127.0.0.1:8080"]

    model_config = SettingsConfigDict(
        env_file="backend/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
