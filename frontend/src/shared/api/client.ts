export type TemplateStatus = {
  manifestExists: boolean;
  indexExists: boolean;
  productCount: number;
  imageCount: number;
  manifestPath: string;
  indexPath: string;
  sources?: TemplateSource[];
};

export type TemplateSource = {
  filename: string;
  size: number;
  updatedAt: number;
  built: boolean;
};

export type SystemStatus = {
  service: string;
  models: {
    embeddingModel: string;
    defaultModelPlatform?: string;
    vlModel: string;
    apiKeyConfigured: boolean;
    volcApiKeyConfigured?: boolean;
  };
  templates: TemplateStatus;
};

export type OpenApiTokenStatus = {
  name: string;
  enabled: boolean;
  source: string;
  maskedKey: string;
};

export type OpenApiStatus = {
  configured: boolean;
  keys: OpenApiTokenStatus[];
};

export type GeneratedOpenApiToken = {
  configured: boolean;
  name: string;
  key: string;
  source: string;
  maskedKey: string;
};

export type RecognitionMatch = {
  score: number;
  product_code: string;
  product_name: string;
  package_type: string;
  view: string;
  image_path: string;
  template_image_url: string | null;
  source_workbook: string;
  sheet: string;
  row: number;
  visual_score: number;
  brand_score?: number;
  text_score: number;
  package_score: number;
  weights?: Record<string, number>;
  matched_keywords: string[];
};

export type RecognitionResponse = {
  filename: string;
  traceId?: string;
  best: RecognitionMatch | null;
  candidates: RecognitionMatch[];
  reviewRequired: boolean;
  analysis: {
    source: string;
    packageType: string | null;
    keywords: string[];
    brands: string[];
    productText: string[];
    isMultiProduct: boolean;
    primaryProductDescription: string;
    manualHints: string[];
    apiKeySource: string;
    modelProfile?: string;
    modelCalls?: ModelCallLog[];
    hasCompetitorBrand?: boolean;
    footerCropped?: boolean;
    matchedSnowBrands?: string[];
    matchedCompetitorBrands?: string[];
  };
  pipeline: {
    stage1: {
      name: string;
      packageType: string | null;
      candidateCount: number;
      fallback: boolean;
    };
    stage2: {
      name: string;
      keywords: string[];
      candidateCount: number;
      fallback: boolean;
    };
    stage3: {
      name: string;
      candidateCount: number;
    };
  };
  models: {
    embeddingModel: string;
    vlModel: string;
    enableVlRerank: boolean;
    qwenTimeoutSeconds: number;
  };
};

export type WorkbookImageLink = {
  row: number;
  sheet: string;
  image_url: string;
};

export type WorkbookLinksResponse = {
  filename: string;
  field: string;
  count: number;
  links: WorkbookImageLink[];
};

export type BatchExportRow = {
  trace_id?: string;
  source: string;
  status: string;
  product_code: string;
  product_name: string;
  package_type: string;
  score: number | null;
  sheet?: string;
  row?: number | null;
  error?: string;
};

export type ModelSettings = {
  embedding_model: string;
  default_model_platform: string;
  vl_model: string;
  task_model_profile: string;
  model_profiles: string;
  business_strategies?: BusinessStrategy[];
  model_configs: ModelConfig[];
  enable_vl_rerank: boolean;
  low_confidence_threshold: number;
  top_k: number;
  qwen_timeout_seconds: number;
  weight_brand_match_visual: number;
  weight_brand_match_brand: number;
  weight_brand_match_text: number;
  weight_brand_miss_visual: number;
  weight_brand_miss_text: number;
  weight_no_brand_visual: number;
  weight_no_brand_text: number;
  snow_brand_names: string;
  vision_prompt: string;
  dashscope_api_key?: string;
  volc_api_key?: string;
  source: string;
  api_key_configured: boolean;
  volc_api_key_configured: boolean;
  embedding_index_needs_rebuild: boolean;
};

export type ModelConfig = {
  id: string;
  name: string;
  enabled: boolean;
  provider: string;
  base_url: string;
  model: string;
  node_models: NodeModels;
  api_key?: string;
  api_key_configured?: boolean;
  business_profile?: "default" | "fallback" | "high_accuracy";
  strategy_id?: string;
  use_as_default?: boolean;
};

export type NodeModels = {
  default: string;
  brand_package: string;
  ocr_text: string;
  final_judge: string;
};

export type BusinessStrategy = {
  id: string;
  name: string;
  enabled: boolean;
  type: "default" | "fallback" | "high_accuracy";
  fallback_model_ids: string[];
  brand_package_model_id: string;
  ocr_text_model_id: string;
  final_judge_model_id: string;
};

export type RecognitionLog = {
  id: string;
  sequence?: number;
  traceId?: string;
  createdAt: string;
  filename: string;
  status: string;
  analysisSource: string;
  gate: {
    hasSnowBrand: boolean;
    hasCompetitorBrand: boolean;
    matchedSnowBrands?: string[];
    matchedCompetitorBrands?: string[];
    footerCropped?: boolean;
    reason: string;
    cleanedTexts: string[];
  };
  pipeline: RecognitionResponse["pipeline"];
  best: RecognitionLogCandidate | null;
  candidates: RecognitionLogCandidate[];
  modelCalls?: ModelCallLog[];
  reviewRequired: boolean;
  matchReason: string;
};

export type ModelCallLog = {
  role: string;
  provider?: string;
  model: string;
  attempt: number;
  source: string;
  elapsedMs: number;
  brands?: string[];
  keywords?: string[];
  productText?: string[];
  rawText?: string;
};

export type ModelTestResponse = {
  ok: boolean;
  provider: string;
  model: string;
  endpoint: string;
  apiKeySource: string;
  elapsedMs: number;
  message: string;
};

export type RecognitionLogsResponse = {
  logs: RecognitionLog[];
  total: number;
  page: number;
  pageSize: number;
};

export type RecognitionLogFilters = {
  q?: string;
  status?: "all" | "命中" | "未命中" | "鍛戒腑" | "鏈懡涓?";
  snowGate?: "all" | "pass" | "fail";
  competitor?: "all" | "yes" | "no";
};

export type RecognitionLogCandidate = {
  productCode: string;
  productName: string;
  packageType: string;
  view: string;
  templateImageUrl: string | null;
  score: number;
  visualScore: number;
  brandScore: number;
  textScore: number;
  matchedKeywords: string[];
  reason: string;
};

export type TemplateUploadResponse = {
  uploadedFiles: string[];
  productCount: number;
  indexedImageCount: number;
  sources: TemplateSource[];
  status: TemplateStatus;
};

export async function fetchSystemStatus(): Promise<SystemStatus> {
  const response = await fetch("/api/status");
  if (!response.ok) {
    throw new Error(`鐘舵€佹帴鍙ｈ姹傚け璐ワ細${response.status}`);
  }
  return response.json();
}

export async function fetchOpenApiStatus(): Promise<OpenApiStatus> {
  const response = await fetch("/api/open/status");
  if (!response.ok) {
    throw new Error(`寮€鏀炬帴鍙ｇ姸鎬佽姹傚け璐ワ細${response.status}`);
  }
  return response.json();
}

export async function generateOpenApiToken(name = "default"): Promise<GeneratedOpenApiToken> {
  const response = await fetch("/api/open/tokens", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name })
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail ?? `寮€鏀炬帴鍙?Token 鐢熸垚澶辫触锛?{response.status}`);
  }
  return response.json();
}

function apiKeyHeaders(apiKey?: string): Record<string, string> {
  return apiKey?.trim() ? { "X-DashScope-Api-Key": apiKey.trim() } : {};
}


export async function recognizeImage(
  file: File,
  hints = "",
  apiKey = "",
  traceId = "",
  modelProfile = "default"
): Promise<RecognitionResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("hints", hints);
  formData.append("trace_id", traceId);
  formData.append("model_profile", modelProfile);
  const response = await fetch("/api/recognize", {
    method: "POST",
    headers: apiKeyHeaders(apiKey),
    body: formData
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail ?? `璇嗗埆鎺ュ彛璇锋眰澶辫触锛?{response.status}`);
  }
  return response.json();
}

export async function recognizeImageUrl(
  imageUrl: string,
  hints = "",
  apiKey = "",
  traceId = "",
  modelProfile = "default"
): Promise<RecognitionResponse> {
  const response = await fetch("/api/recognize-url", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...apiKeyHeaders(apiKey) },
    body: JSON.stringify({ image_url: imageUrl, hints, trace_id: traceId, model_profile: modelProfile })
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail ?? `鍥剧墖閾炬帴璇嗗埆澶辫触锛?{response.status}`);
  }
  return response.json();
}

export async function extractWorkbookImageLinks(file: File): Promise<WorkbookLinksResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch("/api/recognize-url-workbook", {
    method: "POST",
    body: formData
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail ?? `琛ㄦ牸閾炬帴璇诲彇澶辫触锛?{response.status}`);
  }
  return response.json();
}

export async function exportBatchResults(rows: BatchExportRow[]): Promise<Blob> {
  const response = await fetch("/api/batch-results/export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rows })
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail ?? `鎵归噺缁撴灉瀵煎嚭澶辫触锛?{response.status}`);
  }
  return response.blob();
}

export async function fetchModelSettings(): Promise<ModelSettings> {
  const response = await fetch("/api/settings/models");
  if (!response.ok) {
    throw new Error(`妯″瀷閰嶇疆璇锋眰澶辫触锛?{response.status}`);
  }
  return response.json();
}

export async function fetchRecognitionLogs(page = 1, pageSize = 50, filters: RecognitionLogFilters = {}): Promise<RecognitionLogsResponse> {
  const params = new URLSearchParams({
    page: String(page),
    pageSize: String(pageSize),
    q: filters.q ?? "",
    status: filters.status ?? "all",
    snowGate: filters.snowGate ?? "all",
    competitor: filters.competitor ?? "all"
  });
  const response = await fetch(`/api/logs/recognition?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`璇嗗埆鏃ュ織璇锋眰澶辫触锛?{response.status}`);
  }
  return response.json();
}

export async function clearRecognitionLogs(): Promise<{ ok: boolean }> {
  const response = await fetch("/api/logs/recognition", {
    method: "DELETE"
  });
  if (!response.ok) {
    throw new Error(`璇嗗埆鏃ュ織娓呯┖澶辫触锛?{response.status}`);
  }
  return response.json();
}

export async function exportRecognitionLogs(filters: RecognitionLogFilters = {}, ids: string[] = []): Promise<Blob> {
  const params = new URLSearchParams({
    q: filters.q ?? "",
    status: filters.status ?? "all",
    snowGate: filters.snowGate ?? "all",
    competitor: filters.competitor ?? "all"
  });
  if (ids.length) {
    params.set("ids", ids.join(","));
  }
  const response = await fetch(`/api/logs/recognition/export?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`璇嗗埆鏃ュ織瀵煎嚭澶辫触锛?{response.status}`);
  }
  return response.blob();
}

export async function updateModelSettings(payload: {
  embedding_model: string;
  default_model_platform: string;
  vl_model: string;
  task_model_profile: string;
  model_profiles: string;
  business_strategies?: BusinessStrategy[];
  model_configs: ModelConfig[];
  enable_vl_rerank: boolean;
  low_confidence_threshold: number;
  top_k: number;
  qwen_timeout_seconds: number;
  weight_brand_match_visual: number;
  weight_brand_match_brand: number;
  weight_brand_match_text: number;
  weight_brand_miss_visual: number;
  weight_brand_miss_text: number;
  weight_no_brand_visual: number;
  weight_no_brand_text: number;
  snow_brand_names: string;
  vision_prompt: string;
  dashscope_api_key?: string;
  volc_api_key?: string;
}): Promise<ModelSettings> {
  const response = await fetch("/api/settings/models", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail ?? `妯″瀷閰嶇疆淇濆瓨澶辫触锛?{response.status}`);
  }
  return response.json();
}

export async function resetModelSettings(): Promise<ModelSettings> {
  const response = await fetch("/api/settings/models/reset", {
    method: "POST"
  });
  if (!response.ok) {
    throw new Error(`妯″瀷閰嶇疆鎭㈠澶辫触锛?{response.status}`);
  }
  return response.json();
}

export async function testModelConnection(payload: {
  provider: string;
  model: string;
  config_id?: string;
  config_name?: string;
  base_url?: string;
  api_key?: string;
  timeout_seconds?: number;
}): Promise<ModelTestResponse> {
  const response = await fetch("/api/settings/models/test", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail ?? `妯″瀷娴嬭瘯澶辫触锛?{response.status}`);
  }
  return response.json();
}

export async function uploadTemplateWorkbooks(files: File[]): Promise<TemplateUploadResponse> {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }
  const response = await fetch("/api/templates/upload", {
    method: "POST",
    body: formData
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail ?? `妯℃澘搴撲笂浼犲け璐ワ細${response.status}`);
  }
  return response.json();
}

export async function fetchTemplateSources(): Promise<{ sources: TemplateSource[]; status: TemplateStatus }> {
  const response = await fetch("/api/templates/sources");
  if (!response.ok) {
    throw new Error(`妯℃澘婧愭枃浠惰姹傚け璐ワ細${response.status}`);
  }
  return response.json();
}

export async function deleteTemplateSource(filename: string): Promise<TemplateUploadResponse & { deletedFile: string }> {
  const response = await fetch(`/api/templates/sources/${encodeURIComponent(filename)}`, {
    method: "DELETE"
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail ?? `妯℃澘婧愭枃浠跺垹闄ゅけ璐ワ細${response.status}`);
  }
  return response.json();
}

export async function downloadTemplateSource(filename: string): Promise<Blob> {
  const response = await fetch(`/api/templates/sources/${encodeURIComponent(filename)}/download`);
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail ?? `妯℃澘婧愭枃浠朵笅杞藉け璐ワ細${response.status}`);
  }
  return response.blob();
}

export function getTemplateSourceDownloadUrl(filename: string): string {
  return `/api/templates/sources/${encodeURIComponent(filename)}/download`;
}
