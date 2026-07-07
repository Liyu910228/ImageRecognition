import { useState } from "react";
import { FlaskConical, Plus, Settings2, Trash2 } from "lucide-react";
import {
  testModelConnection,
  type ModelConfig,
  type ModelSettings,
  type ModelTestResponse,
  type NodeModels
} from "../../shared/api/client";

type TestState = {
  status: "idle" | "testing" | "success" | "error";
  message: string;
  result: ModelTestResponse | null;
};

const NODE_LABELS: Array<{ key: keyof NodeModels; label: string; hint: string }> = [
  { key: "default", label: "综合识别节点", hint: "默认识别用模型" },
  { key: "brand_package", label: "品牌/包装节点", hint: "识别品牌、包装类型、主商品" },
  { key: "ocr_text", label: "OCR/文字节点", hint: "识别包装文字、规格、度数、容量" },
  { key: "final_judge", label: "最终判断节点", hint: "融合前两个节点结果做最终判断" }
];

export function ModelSettingsPanel({
  modelSettings,
  modelMessage,
  frontendApiKey,
  backendApiKeyInput,
  backendVolcApiKeyInput,
  setFrontendApiKey,
  setBackendApiKeyInput,
  setBackendVolcApiKeyInput,
  setModelMessage,
  handleModelChange,
  handleSaveModels,
  handleResetModels
}: {
  modelSettings: ModelSettings | null;
  modelMessage: string;
  frontendApiKey: string;
  backendApiKeyInput: string;
  backendVolcApiKeyInput: string;
  setFrontendApiKey: (value: string) => void;
  setBackendApiKeyInput: (value: string) => void;
  setBackendVolcApiKeyInput: (value: string) => void;
  setModelMessage: (value: string) => void;
  handleModelChange: (field: keyof ModelSettings, value: string | boolean | number | ModelConfig[]) => void;
  handleSaveModels: () => void;
  handleResetModels: () => void;
}) {
  const [tests, setTests] = useState<Record<string, TestState>>({});
  const configs = modelSettings?.model_configs?.length ? modelSettings.model_configs : [];

  const percentValue = (field: keyof ModelSettings, fallback: number) => Math.round(Number(modelSettings?.[field] ?? fallback) * 100);
  const updatePercent = (field: keyof ModelSettings, value: string) => {
    const numericValue = Number(value);
    void handleModelChange(field, Number.isFinite(numericValue) ? numericValue / 100 : 0);
  };

  function updateConfig(index: number, patch: Partial<ModelConfig>) {
    const next = configs.map((item, itemIndex) => {
      if (itemIndex === index) {
        return { ...item, ...patch };
      }
      return patch.use_as_default ? { ...item, use_as_default: false } : item;
    });
    void handleModelChange("model_configs", next);
    setModelMessage("");
  }

  function updateNodeModel(index: number, node: keyof NodeModels, value: string) {
    const config = configs[index];
    updateConfig(index, {
      node_models: {
        ...withNodeModels(config),
        [node]: value
      }
    });
  }

  function addConfig() {
    const nextIndex = configs.length + 1;
    const provider = modelSettings?.default_model_platform ?? "aliyun";
    const model = provider === "volc" ? "ep-xxx" : "qwen3-vl-plus";
    const next: ModelConfig = {
      id: `model_${Date.now()}`,
      name: `模型 ${nextIndex}`,
      enabled: true,
      provider,
      base_url: provider === "volc" ? "https://ark.cn-beijing.volces.com/api/v3/chat/completions" : "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
      model,
      node_models: defaultNodeModels(model),
      api_key: "",
      api_key_configured: false,
      use_as_default: configs.length === 0
    };
    void handleModelChange("model_configs", [...configs, next]);
    setModelMessage("");
  }

  function deleteConfig(index: number) {
    void handleModelChange("model_configs", configs.filter((_, itemIndex) => itemIndex !== index));
    setModelMessage("");
  }

  async function testNode(config: ModelConfig, node: keyof NodeModels) {
    const nodeModels = withNodeModels(config);
    const model = nodeModels[node] || config.model;
    const key = `${config.id || config.name}:${node}`;
    setTests((current) => ({ ...current, [key]: { status: "testing", message: "测试中...", result: null } }));
    try {
      const result = await testModelConnection({
        provider: config.provider,
        model,
        config_id: config.id,
        config_name: config.name,
        base_url: config.base_url,
        api_key: config.api_key?.trim() || undefined,
        timeout_seconds: Number(modelSettings?.qwen_timeout_seconds ?? 10)
      });
      setTests((current) => ({
        ...current,
        [key]: {
          status: result.ok ? "success" : "error",
          message: result.ok ? "测试成功：连接成功" : "测试失败",
          result
        }
      }));
    } catch (error) {
      setTests((current) => ({
        ...current,
        [key]: {
          status: "error",
          message: error instanceof Error ? error.message : "测试失败",
          result: null
        }
      }));
    }
  }

  return (
    <div className="panel model-management-panel">
      <div className="panel-heading inline-heading">
        <div>
          <h2>模型管理</h2>
          <p>维护平台地址、API Key 和各业务节点模型；业务员自动使用当前默认平台配置。</p>
        </div>
        <Settings2 size={18} />
      </div>

      <div className="settings-form">
        <div className="model-config-toolbar">
          <div>
            <strong>平台模型块</strong>
            <small className="field-hint">每个平台独立配置四个业务节点；模型失败统一回退本地视觉识别。</small>
          </div>
          <button className="secondary-action" type="button" onClick={addConfig}>
            <Plus size={16} />
            新增平台
          </button>
        </div>

        <div className="model-config-list">
          {configs.map((config, index) => {
            const nodes = withNodeModels(config);
            return (
              <section className="model-config-card" key={config.id || `${config.name}-${index}`}>
                <div className="model-config-card-head">
                  <label className="model-config-enable">
                    <input
                      type="checkbox"
                      checked={config.enabled}
                      onChange={(event) => updateConfig(index, { enabled: event.target.checked })}
                    />
                    启用
                  </label>
                  <strong>{config.name || `模型 ${index + 1}`}</strong>
                  <div className="model-config-actions">
                    <button className="danger-icon-button" type="button" onClick={() => deleteConfig(index)} aria-label="删除平台">
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>

                <div className="model-config-grid">
                  <label>
                    <span>配置名称</span>
                    <input value={config.name} onChange={(event) => updateConfig(index, { name: event.target.value })} />
                  </label>
                  <label>
                    <span>平台</span>
                    <select
                      value={config.provider}
                      onChange={(event) => {
                        const provider = event.target.value;
                        const model = provider === "volc" ? "ep-xxx" : "qwen3-vl-plus";
                        updateConfig(index, {
                          provider,
                          base_url: provider === "volc" ? "https://ark.cn-beijing.volces.com/api/v3/chat/completions" : "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                          model,
                          node_models: defaultNodeModels(model)
                        });
                      }}
                    >
                      <option value="aliyun">阿里</option>
                      <option value="volc">火山</option>
                    </select>
                  </label>
                  <label className="wide-field">
                    <span>模型地址</span>
                    <input value={config.base_url} onChange={(event) => updateConfig(index, { base_url: event.target.value })} />
                  </label>
                  <label>
                    <span>API Key</span>
                    <input
                      type="password"
                      value={config.api_key ?? ""}
                      onChange={(event) => updateConfig(index, { api_key: event.target.value })}
                      placeholder={config.api_key_configured ? "已配置，留空保持不变" : "填写当前平台 Key"}
                    />
                  </label>
                  <label>
                    <span>默认模型名</span>
                    <input
                      value={config.model}
                      onChange={(event) => updateConfig(index, { model: event.target.value, node_models: normalizeNodeModels(nodes, event.target.value) })}
                      placeholder={config.provider === "volc" ? "ep-xxx 或 doubao-seed-2-0-pro-260215" : "qwen3-vl-plus"}
                    />
                  </label>
                  <label className="model-default-toggle">
                    <span>业务默认</span>
                    <button
                      className={config.use_as_default ? "secondary-action active-default" : "secondary-action"}
                      type="button"
                      disabled={!config.enabled}
                      onClick={() => updateConfig(index, { use_as_default: true })}
                    >
                      {config.use_as_default ? "当前默认" : "设为默认"}
                    </button>
                  </label>
                </div>

                <div className="settings-subsection node-model-heading">
                  <strong>业务节点模型</strong>
                  <small className="field-hint">每个节点可以填写不同模型，并单独测试；识别失败后统一走本地视觉兜底。</small>
                </div>
                <div className="node-model-grid">
                  {NODE_LABELS.map((node) => {
                    const testKey = `${config.id || config.name}:${node.key}`;
                    const test = tests[testKey];
                    return (
                      <div className="node-model-row" key={node.key}>
                        <label>
                          <span>{node.label}</span>
                          <input value={nodes[node.key]} onChange={(event) => updateNodeModel(index, node.key, event.target.value)} />
                          <small className="field-hint">{node.hint}</small>
                        </label>
                        <button className="secondary-action" type="button" onClick={() => void testNode(config, node.key)} disabled={test?.status === "testing"}>
                          <FlaskConical size={16} />
                          {test?.status === "testing" ? "测试中" : "测试"}
                        </button>
                        {test?.message && <span className={test.status === "success" ? "model-test-chip success" : "model-test-chip error"}>{test.message}</span>}
                        {test?.result && (
                          <div className="model-test-result node-test-result">
                            <span>模型：{test.result.model}</span>
                            <span>耗时：{test.result.elapsedMs} ms</span>
                            <span>Key：{test.result.apiKeySource}</span>
                            <pre>{test.result.message}</pre>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                {config.provider === "volc" && (
                  <small className="field-hint">
                    火山 Ark 需要填写控制台接入点 ID（ep-...）或已开通的模型 ID；不要填写 Doubao-Seed-2.0-Pro 这种展示名。
                  </small>
                )}
              </section>
            );
          })}
        </div>

        <div className="settings-subsection">
          <strong>识别参数</strong>
        </div>
        <label>
          <span>向量模型</span>
          <input
            value={modelSettings?.embedding_model ?? ""}
            onChange={(event) => void handleModelChange("embedding_model", event.target.value)}
            placeholder="qwen3-vl-embedding"
          />
        </label>
        <label>
          <span>Top 候选数量</span>
          <input
            type="number"
            min="1"
            max="20"
            step="1"
            value={modelSettings?.top_k ?? 5}
            onChange={(event) => void handleModelChange("top_k", Number(event.target.value))}
          />
        </label>
        <label>
          <span>模型超时时间（秒）</span>
          <input
            type="number"
            min="1"
            max="120"
            step="1"
            value={modelSettings?.qwen_timeout_seconds ?? 10}
            onChange={(event) => void handleModelChange("qwen_timeout_seconds", Number(event.target.value))}
          />
        </label>
        <label>
          <span>低置信度阈值</span>
          <input
            type="number"
            min="0"
            max="1"
            step="0.01"
            value={modelSettings?.low_confidence_threshold ?? 0.72}
            onChange={(event) => void handleModelChange("low_confidence_threshold", Number(event.target.value))}
          />
        </label>

        <div className="settings-subsection">
          <strong>匹配权重（百分比）</strong>
        </div>
        <div className="weight-grid">
          <WeightInput label="有品牌且命中 · 视觉" value={percentValue("weight_brand_match_visual", 0.2)} onChange={(value) => updatePercent("weight_brand_match_visual", value)} />
          <WeightInput label="有品牌且命中 · 品牌" value={percentValue("weight_brand_match_brand", 0.55)} onChange={(value) => updatePercent("weight_brand_match_brand", value)} />
          <WeightInput label="有品牌且命中 · 关键词" value={percentValue("weight_brand_match_text", 0.25)} onChange={(value) => updatePercent("weight_brand_match_text", value)} />
          <WeightInput label="有品牌但未命中 · 视觉" value={percentValue("weight_brand_miss_visual", 0.8)} onChange={(value) => updatePercent("weight_brand_miss_visual", value)} />
          <WeightInput label="有品牌但未命中 · 关键词" value={percentValue("weight_brand_miss_text", 0.2)} onChange={(value) => updatePercent("weight_brand_miss_text", value)} />
          <WeightInput label="无品牌 · 视觉" value={percentValue("weight_no_brand_visual", 0.85)} onChange={(value) => updatePercent("weight_no_brand_visual", value)} />
          <WeightInput label="无品牌 · 关键词" value={percentValue("weight_no_brand_text", 0.15)} onChange={(value) => updatePercent("weight_no_brand_text", value)} />
        </div>

        <label>
          <span>雪花品牌配置</span>
          <textarea
            className="compact-textarea"
            value={modelSettings?.snow_brand_names ?? ""}
            onChange={(event) => void handleModelChange("snow_brand_names", event.target.value)}
          />
        </label>
        <label>
          <span>图片提示词</span>
          <textarea
            value={modelSettings?.vision_prompt ?? ""}
            onChange={(event) => void handleModelChange("vision_prompt", event.target.value)}
          />
        </label>

        <label>
          <span>前端临时阿里 Key</span>
          <input
            type="password"
            value={frontendApiKey}
            onChange={(event) => {
              setFrontendApiKey(event.target.value);
              setModelMessage("");
            }}
            placeholder="不填则使用模型块或后端默认 Key"
          />
        </label>

        <label className="legacy-key-row">
          <span>旧版阿里 Key</span>
          <input
            type="password"
            value={backendApiKeyInput}
            onChange={(event) => setBackendApiKeyInput(event.target.value)}
            placeholder="兼容旧配置；建议改用上方平台 Key"
          />
        </label>
        <label className="legacy-key-row">
          <span>旧版火山 Key</span>
          <input
            type="password"
            value={backendVolcApiKeyInput}
            onChange={(event) => setBackendVolcApiKeyInput(event.target.value)}
            placeholder="兼容旧配置；建议改用上方平台 Key"
          />
        </label>

        <label className="toggle-row">
          <span>启用多节点复核</span>
          <input
            type="checkbox"
            checked={modelSettings?.enable_vl_rerank ?? true}
            onChange={(event) => void handleModelChange("enable_vl_rerank", event.target.checked)}
          />
        </label>

        <div className="settings-actions">
          <button className="primary-action" type="button" onClick={handleSaveModels}>
            保存配置
          </button>
          <button className="secondary-action" type="button" onClick={handleResetModels}>
            恢复默认
          </button>
        </div>
        {modelSettings?.embedding_index_needs_rebuild && (
          <div className="inline-error">向量模型已变化，后续需要重建模板索引。</div>
        )}
        {modelMessage && <p className="model-note">{modelMessage}</p>}
      </div>
    </div>
  );
}

function WeightInput({ label, value, onChange }: { label: string; value: number; onChange: (value: string) => void }) {
  return (
    <label>
      <span>{label}</span>
      <input
        type="number"
        min="0"
        max="100"
        step="1"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

function defaultNodeModels(model: string): NodeModels {
  return {
    default: model,
    brand_package: model,
    ocr_text: model,
    final_judge: model
  };
}

function withNodeModels(config: ModelConfig): NodeModels {
  return normalizeNodeModels(config.node_models, config.model);
}

function normalizeNodeModels(nodeModels: Partial<NodeModels> | undefined, model: string): NodeModels {
  const fallback = model || "qwen3-vl-plus";
  return {
    default: nodeModels?.default || fallback,
    brand_package: nodeModels?.brand_package || fallback,
    ocr_text: nodeModels?.ocr_text || fallback,
    final_judge: nodeModels?.final_judge || fallback
  };
}
