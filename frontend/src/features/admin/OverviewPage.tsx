import { Boxes, Database, FileImage, KeyRound, ListChecks, ScrollText } from "lucide-react";
import type { OpenApiStatus, RecognitionLog, SystemStatus, TemplateSource } from "../../shared/api/client";

export function OverviewPage({
  status,
  templateSources,
  logs,
  openApiStatus
}: {
  status: SystemStatus | null;
  templateSources: TemplateSource[];
  logs: RecognitionLog[];
  openApiStatus: OpenApiStatus | null;
}) {
  const templates = status?.templates;
  return (
    <div className="module-page">
      <div className="module-header">
        <div>
          <h2>工作概览</h2>
          <p>快速查看模板库、模型、日志和开放接口状态。</p>
        </div>
      </div>
      <section className="overview-grid">
        <OverviewCard icon={Database} label="模板产品" value={templates?.productCount ?? "--"} note="Excel 模板库产品数量" />
        <OverviewCard icon={FileImage} label="模板图片" value={templates?.imageCount ?? "--"} note="已索引的模板图片数量" />
        <OverviewCard icon={Boxes} label="模板文件" value={templateSources.length} note="已上传并构建的源文件" />
        <OverviewCard icon={ListChecks} label="模型配置" value={status?.models.vlModel ?? "--"} note={status?.models.defaultModelPlatform ?? "默认平台"} />
        <OverviewCard icon={ScrollText} label="最近日志" value={logs.length} note="当前页加载的识别日志" />
        <OverviewCard icon={KeyRound} label="开放接口" value={openApiStatus?.configured ? "已启用" : "未配置"} note={openApiStatus?.keys[0]?.maskedKey ?? "等待生成 Token"} />
      </section>
      <section className="status-strip module-status-strip" aria-label="系统状态">
        <StatusMetric label="向量索引" value={templates?.indexExists ? "已构建" : "待构建"} tone={templates?.indexExists ? "good" : "warn"} />
        <StatusMetric label="模型 Key" value={status?.models.apiKeyConfigured ? "后端已配置" : "未配置"} tone={status?.models.apiKeyConfigured ? "good" : "warn"} />
        <StatusMetric label="火山 Key" value={status?.models.volcApiKeyConfigured ? "后端已配置" : "未配置"} tone={status?.models.volcApiKeyConfigured ? "good" : "warn"} />
      </section>
    </div>
  );
}

function OverviewCard({
  icon: Icon,
  label,
  value,
  note
}: {
  icon: typeof Database;
  label: string;
  value: string | number;
  note: string;
}) {
  return (
    <div className="overview-card">
      <Icon size={22} />
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  );
}

function StatusMetric({
  label,
  value,
  tone
}: {
  label: string;
  value: string | number;
  tone?: "good" | "warn";
}) {
  return (
    <div className={`metric ${tone ?? ""}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
