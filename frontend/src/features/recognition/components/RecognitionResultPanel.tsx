import type { RecognitionResponse } from "../../../shared/api/client";
import { toPercent } from "../utils";

export function RecognitionResultPanel({ recognition }: { recognition: RecognitionResponse | null }) {
  const best = recognition?.best;

  return (
    <div className="panel result-panel">
      <div className="panel-heading">
        <div>
          <h2>最佳识别结果</h2>
          <p>等待上传图片后显示产品信息</p>
        </div>
      </div>
      <dl className="result-list">
        <ResultRow label="产品编码" value={best?.product_code ?? "--"} />
        <ResultRow label="产品名称" value={best?.product_name ?? "--"} />
        <ResultRow label="瓶/听/箱" value={best?.package_type ?? "--"} />
        <ResultRow label="视角" value={best?.view ?? "--"} />
        <ResultRow label="相似度" value={best ? toPercent(best.score) : "--"} />
      </dl>
      {recognition?.reviewRequired && <div className="review-note">相似度偏低，建议人工复核。</div>}
      {recognition?.analysis && (
        <div className="analysis-box">
          <div className="pipeline-steps">
            <PipelineStep
              index={1}
              title="瓶/听/箱"
              value={recognition.pipeline.stage1.packageType ?? "未判断"}
              count={recognition.pipeline.stage1.candidateCount}
              fallback={recognition.pipeline.stage1.fallback}
            />
            <PipelineStep
              index={2}
              title="品牌信息"
              value={recognition.pipeline.stage2.keywords.slice(0, 4).join(" / ") || "无关键词"}
              count={recognition.pipeline.stage2.candidateCount}
              fallback={recognition.pipeline.stage2.fallback}
            />
            <PipelineStep
              index={3}
              title="图片语义相似度"
              value="候选内排序"
              count={recognition.pipeline.stage3.candidateCount}
            />
          </div>
          <div className="analysis-grid">
            <ResultRow label="识别来源" value={analysisSourceLabel(recognition.analysis.source)} />
            <ResultRow label="先判类型" value={recognition.analysis.packageType ?? "--"} />
            <ResultRow label="多产品" value={recognition.analysis.isMultiProduct ? "是" : "否"} />
          </div>
          <KeywordLine label="品牌" values={recognition.analysis.brands} />
          <KeywordLine label="关键词" values={recognition.analysis.keywords} />
          <KeywordLine label="可见文字" values={recognition.analysis.productText} />
          <KeywordLine label="人工提示" values={recognition.analysis.manualHints} />
          <KeywordLine label="Key来源" values={[apiKeySourceLabel(recognition.analysis.apiKeySource)]} />
        </div>
      )}
      {best?.template_image_url && (
        <div className="template-preview">
          <img src={best.template_image_url} alt="命中模板图" />
        </div>
      )}
    </div>
  );
}

function ResultRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="result-row">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function KeywordLine({ label, values }: { label: string; values: string[] }) {
  return (
    <div className="keyword-line">
      <span>{label}</span>
      <div>
        {values.length ? values.map((value) => <strong key={`${label}-${value}`}>{value}</strong>) : <em>--</em>}
      </div>
    </div>
  );
}

function PipelineStep({
  index,
  title,
  value,
  count,
  fallback
}: {
  index: number;
  title: string;
  value: string;
  count: number;
  fallback?: boolean;
}) {
  return (
    <div className="pipeline-step">
      <span>{index}</span>
      <div>
        <strong>{title}</strong>
        <em>{value}</em>
        <small>{fallback ? "无命中，已回退上一层" : `候选 ${count}`}</small>
      </div>
    </div>
  );
}

function analysisSourceLabel(source: string) {
  if (source === "qwen") {
    return "Qwen视觉理解";
  }
  if (source === "volc") {
    return "火山/豆包视觉理解";
  }
  if (source === "aliyun") {
    return "阿里视觉理解";
  }
  if (source === "no_api_key") {
    return "未配置Key，已退回本地视觉";
  }
  if (source === "model_error" || source === "qwen_error") {
    return "模型调用失败，已退回本地视觉";
  }
  if (source === "model_timeout" || source === "qwen_timeout") {
    return "模型超时，已退回本地视觉";
  }
  if (source === "model_error_local_fallback" || source === "qwen_error_local_fallback") {
    return "模型调用失败，已使用本地视觉兜底";
  }
  if (source === "model_timeout_local_fallback" || source === "qwen_timeout_local_fallback") {
    return "模型超时，已使用本地视觉兜底";
  }
  return source;
}

function apiKeySourceLabel(source: string) {
  if (source === "request") {
    return "前端临时 Key";
  }
  if (source === "runtime") {
    return "后端保存 Key";
  }
  if (source === "env") {
    return "后端环境变量";
  }
  return "未使用 Key";
}
