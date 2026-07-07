from pydantic import BaseModel, Field


class NodeModelsUpdate(BaseModel):
    default: str = ""
    brand_package: str = ""
    ocr_text: str = ""
    final_judge: str = ""


class ModelConfigUpdate(BaseModel):
    id: str = ""
    name: str = Field(min_length=1)
    enabled: bool = True
    provider: str = "aliyun"
    base_url: str = ""
    model: str = Field(min_length=1)
    node_models: NodeModelsUpdate | None = None
    api_key: str | None = None
    business_profile: str = "default"
    strategy_id: str = ""
    use_as_default: bool = False


class BusinessStrategyUpdate(BaseModel):
    id: str = ""
    name: str = ""
    enabled: bool = True
    type: str = "default"
    fallback_model_ids: list[str] = []
    brand_package_model_id: str = ""
    ocr_text_model_id: str = ""
    final_judge_model_id: str = ""


class ModelSettingsUpdate(BaseModel):
    embedding_model: str = Field(min_length=1)
    default_model_platform: str = "aliyun"
    vl_model: str = Field(min_length=1)
    task_model_profile: str = "default"
    model_profiles: str = ""
    business_strategies: list[BusinessStrategyUpdate] = []
    model_configs: list[ModelConfigUpdate] = []
    enable_vl_rerank: bool = True
    low_confidence_threshold: float = Field(default=0.72, ge=0, le=1)
    top_k: int = Field(default=5, ge=1, le=20)
    qwen_timeout_seconds: int = Field(default=10, ge=1, le=120)
    weight_brand_match_visual: float = Field(default=0.2, ge=0, le=1)
    weight_brand_match_brand: float = Field(default=0.55, ge=0, le=1)
    weight_brand_match_text: float = Field(default=0.25, ge=0, le=1)
    weight_brand_miss_visual: float = Field(default=0.8, ge=0, le=1)
    weight_brand_miss_text: float = Field(default=0.2, ge=0, le=1)
    weight_no_brand_visual: float = Field(default=0.85, ge=0, le=1)
    weight_no_brand_text: float = Field(default=0.15, ge=0, le=1)
    snow_brand_names: str = ""
    vision_prompt: str = ""
    dashscope_api_key: str | None = None
    volc_api_key: str | None = None


class ModelTestRequest(BaseModel):
    provider: str = "aliyun"
    model: str = Field(min_length=1)
    config_id: str = ""
    config_name: str = ""
    base_url: str = ""
    api_key: str | None = None
    timeout_seconds: int = Field(default=10, ge=1, le=120)
