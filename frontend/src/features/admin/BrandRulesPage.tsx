import type { ModelConfig, ModelSettings } from "../../shared/api/client";
import type { useModelSettings } from "../settings/useModelSettings";

type ModelSettingsState = ReturnType<typeof useModelSettings>;

export function BrandRulesPage({ settings }: { settings: ModelSettingsState }) {
  const modelSettings = settings.modelSettings;
  const update = (field: keyof ModelSettings, value: string | boolean | number | ModelConfig[]) => {
    settings.handleModelChange(field, value);
  };

  return (
    <div className="module-page">
      <div className="module-header">
        <div>
          <h2>品牌规则</h2>
          <p>维护雪花体系品牌、图片提示词、Top 候选数量、超时和融合权重。</p>
        </div>
        <button className="primary-action" type="button" onClick={() => void settings.handleSaveModels()}>
          保存规则
        </button>
      </div>
      <div className="panel">
        {!modelSettings ? (
          <div className="empty-source">模型设置加载中...</div>
        ) : (
          <div className="settings-form brand-rules-form">
            <label className="wide-field">
              <span>雪花体系品牌</span>
              <textarea
                rows={4}
                value={modelSettings.snow_brand_names}
                onChange={(event) => update("snow_brand_names", event.target.value)}
                placeholder="雪花、纯生、勇闯天涯、SuperX、AMSTEL..."
              />
            </label>
            <label className="wide-field">
              <span>图片提示词</span>
              <textarea
                rows={8}
                value={modelSettings.vision_prompt}
                onChange={(event) => update("vision_prompt", event.target.value)}
                placeholder="默认用于识别雪花品牌、瓶听箱、可见文字和竞品混合情况"
              />
            </label>
            <div className="settings-grid compact-grid">
              <NumberField label="Top 候选数量" value={modelSettings.top_k} onChange={(value) => update("top_k", value)} />
              <NumberField label="模型超时秒数" value={modelSettings.qwen_timeout_seconds} onChange={(value) => update("qwen_timeout_seconds", value)} />
              <NumberField label="低置信阈值" value={modelSettings.low_confidence_threshold} step={0.01} onChange={(value) => update("low_confidence_threshold", value)} />
            </div>
            <div className="settings-grid compact-grid">
              <NumberField label="品牌命中-视觉权重" value={modelSettings.weight_brand_match_visual} step={0.01} onChange={(value) => update("weight_brand_match_visual", value)} />
              <NumberField label="品牌命中-品牌权重" value={modelSettings.weight_brand_match_brand} step={0.01} onChange={(value) => update("weight_brand_match_brand", value)} />
              <NumberField label="品牌命中-文本权重" value={modelSettings.weight_brand_match_text} step={0.01} onChange={(value) => update("weight_brand_match_text", value)} />
              <NumberField label="品牌缺失-视觉权重" value={modelSettings.weight_brand_miss_visual} step={0.01} onChange={(value) => update("weight_brand_miss_visual", value)} />
              <NumberField label="品牌缺失-文本权重" value={modelSettings.weight_brand_miss_text} step={0.01} onChange={(value) => update("weight_brand_miss_text", value)} />
              <NumberField label="无品牌-视觉权重" value={modelSettings.weight_no_brand_visual} step={0.01} onChange={(value) => update("weight_no_brand_visual", value)} />
              <NumberField label="无品牌-文本权重" value={modelSettings.weight_no_brand_text} step={0.01} onChange={(value) => update("weight_no_brand_text", value)} />
            </div>
            {settings.modelMessage && <p className="model-note">{settings.modelMessage}</p>}
          </div>
        )}
      </div>
    </div>
  );
}

function NumberField({
  label,
  value,
  step = 1,
  onChange
}: {
  label: string;
  value: number;
  step?: number;
  onChange: (value: number) => void;
}) {
  return (
    <label>
      <span>{label}</span>
      <input
        type="number"
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </label>
  );
}
