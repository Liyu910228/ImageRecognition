import { useState } from "react";
import {
  fetchModelSettings,
  resetModelSettings,
  updateModelSettings,
  type ModelConfig,
  type ModelSettings
} from "../../shared/api/client";

export function useModelSettings(onStatusChanged?: () => Promise<void> | void) {
  const [modelSettings, setModelSettings] = useState<ModelSettings | null>(null);
  const [modelMessage, setModelMessage] = useState("");
  const [frontendApiKey, setFrontendApiKeyState] = useState(() => sessionStorage.getItem("dashscopeApiKey") ?? "");
  const [backendApiKeyInput, setBackendApiKeyInput] = useState("");
  const [backendVolcApiKeyInput, setBackendVolcApiKeyInput] = useState("");

  async function loadModelSettings() {
    setModelSettings(await fetchModelSettings());
  }

  function setFrontendApiKey(value: string) {
    setFrontendApiKeyState(value);
  }

  function handleModelChange(field: keyof ModelSettings, value: string | boolean | number | ModelConfig[]) {
    setModelSettings((current) => (current ? { ...current, [field]: value } : current));
    setModelMessage("");
  }

  async function handleSaveModels() {
    if (!modelSettings) {
      return;
    }
    const active = modelSettings.model_configs.find((config) => config.enabled && config.use_as_default) ?? modelSettings.model_configs.find((config) => config.enabled);
    setModelMessage("保存中...");
    try {
      const saved = await updateModelSettings({
        embedding_model: modelSettings.embedding_model,
        default_model_platform: modelSettings.default_model_platform,
        vl_model: modelSettings.vl_model,
        task_model_profile: active?.id ?? "default",
        model_profiles: "",
        business_strategies: [],
        model_configs: modelSettings.model_configs,
        enable_vl_rerank: modelSettings.enable_vl_rerank,
        low_confidence_threshold: Number(modelSettings.low_confidence_threshold),
        top_k: Number(modelSettings.top_k),
        qwen_timeout_seconds: Number(modelSettings.qwen_timeout_seconds),
        weight_brand_match_visual: Number(modelSettings.weight_brand_match_visual),
        weight_brand_match_brand: Number(modelSettings.weight_brand_match_brand),
        weight_brand_match_text: Number(modelSettings.weight_brand_match_text),
        weight_brand_miss_visual: Number(modelSettings.weight_brand_miss_visual),
        weight_brand_miss_text: Number(modelSettings.weight_brand_miss_text),
        weight_no_brand_visual: Number(modelSettings.weight_no_brand_visual),
        weight_no_brand_text: Number(modelSettings.weight_no_brand_text),
        snow_brand_names: modelSettings.snow_brand_names,
        vision_prompt: modelSettings.vision_prompt,
        dashscope_api_key: backendApiKeyInput.trim() || undefined,
        volc_api_key: backendVolcApiKeyInput.trim() || undefined
      });
      setModelSettings(saved);
      if (frontendApiKey.trim()) {
        sessionStorage.setItem("dashscopeApiKey", frontendApiKey.trim());
      } else {
        sessionStorage.removeItem("dashscopeApiKey");
      }
      setModelMessage("模型配置已保存");
      setBackendApiKeyInput("");
      setBackendVolcApiKeyInput("");
      await onStatusChanged?.();
    } catch (error) {
      setModelMessage(error instanceof Error ? error.message : "模型配置保存失败");
    }
  }

  async function handleResetModels() {
    setModelMessage("恢复中...");
    try {
      const saved = await resetModelSettings();
      setModelSettings(saved);
      setModelMessage("已恢复默认模型");
      await onStatusChanged?.();
    } catch (error) {
      setModelMessage(error instanceof Error ? error.message : "恢复默认配置失败");
    }
  }

  return {
    modelSettings,
    modelMessage,
    frontendApiKey,
    backendApiKeyInput,
    backendVolcApiKeyInput,
    setFrontendApiKey,
    setBackendApiKeyInput,
    setBackendVolcApiKeyInput,
    setModelMessage,
    loadModelSettings,
    handleModelChange,
    handleSaveModels,
    handleResetModels
  };
}
