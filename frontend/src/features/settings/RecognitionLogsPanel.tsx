import { Download, RefreshCw, Trash2 } from "lucide-react";
import type { RecognitionLog, RecognitionLogFilters } from "../../shared/api/client";
import { toPercent } from "../recognition/utils";

export function RecognitionLogsPanel({
  logs,
  selectedLogIds,
  page,
  pageSize,
  total,
  filters,
  logsMessage,
  onRefresh,
  onPageChange,
  onFiltersChange,
  onClear,
  onExportAll,
  onExportSelected,
  onToggleLog,
  onSelectPage,
  onClearSelected
}: {
  logs: RecognitionLog[];
  selectedLogIds: string[];
  page: number;
  pageSize: number;
  total: number;
  filters: RecognitionLogFilters;
  logsMessage: string;
  onRefresh: () => void;
  onPageChange: (page: number) => void;
  onFiltersChange: (filters: RecognitionLogFilters) => void;
  onClear: () => void;
  onExportAll: () => void;
  onExportSelected: () => void;
  onToggleLog: (id: string) => void;
  onSelectPage: () => void;
  onClearSelected: () => void;
}) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const start = total ? (page - 1) * pageSize + 1 : 0;
  const end = Math.min(total, page * pageSize);

  return (
    <div className="panel admin-log-panel">
      <div className="panel-heading inline-heading">
        <div>
          <h2>识别日志</h2>
          <p>查看图片匹配过程、门禁判断和模板命中原因；每页 {pageSize} 条</p>
        </div>
        <div className="table-actions log-selection-actions">
          <span className="selected-log-count">已选 {selectedLogIds.length} 条</span>
          <button className="secondary-action" type="button" onClick={onSelectPage} disabled={!logs.length}>
            本页全选
          </button>
          <button className="secondary-action" type="button" onClick={onClearSelected} disabled={!selectedLogIds.length}>
            清空选择
          </button>
          <button className="secondary-action" type="button" onClick={onRefresh}>
            <RefreshCw size={18} />
            刷新
          </button>
          <button className="secondary-action" type="button" onClick={onExportSelected} disabled={!selectedLogIds.length}>
            <Download size={18} />
            导出选中
          </button>
          <button className="secondary-action" type="button" onClick={onExportAll}>
            <Download size={18} />
            导出全部
          </button>
          <button className="danger-action" type="button" onClick={onClear}>
            <Trash2 size={16} />
            清空
          </button>
        </div>
      </div>
      {logsMessage && <p className="model-note template-message">{logsMessage}</p>}
      <div className="log-filter-bar">
        <label className="log-search-field">
          <span>查找</span>
          <input
            value={filters.q ?? ""}
            onChange={(event) => onFiltersChange({ ...filters, q: event.target.value })}
            placeholder="识别编号、文件名、产品名、品牌、清洗文字"
          />
        </label>
        <label>
          <span>状态</span>
          <select value={filters.status ?? "all"} onChange={(event) => onFiltersChange({ ...filters, status: event.target.value as RecognitionLogFilters["status"] })}>
            <option value="all">全部</option>
            <option value="命中">命中</option>
            <option value="未命中">未命中</option>
          </select>
        </label>
        <label>
          <span>品牌门禁</span>
          <select value={filters.snowGate ?? "all"} onChange={(event) => onFiltersChange({ ...filters, snowGate: event.target.value as RecognitionLogFilters["snowGate"] })}>
            <option value="all">全部</option>
            <option value="pass">通过</option>
            <option value="fail">未通过</option>
          </select>
        </label>
        <label>
          <span>竞品/混合图</span>
          <select value={filters.competitor ?? "all"} onChange={(event) => onFiltersChange({ ...filters, competitor: event.target.value as RecognitionLogFilters["competitor"] })}>
            <option value="all">全部</option>
            <option value="yes">是</option>
            <option value="no">否</option>
          </select>
        </label>
        <button className="text-action" type="button" onClick={() => onFiltersChange({ q: "", status: "all", snowGate: "all", competitor: "all" })}>
          重置
        </button>
      </div>
      <div className="log-pagination">
        <span>共 {total} 条，当前 {start}-{end}</span>
        <div>
          <button className="text-action" type="button" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
            上一页
          </button>
          <strong>
            {page} / {totalPages}
          </strong>
          <button className="text-action" type="button" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>
            下一页
          </button>
        </div>
      </div>
      <div className="recognition-log-list">
        {logs.length ? (
          logs.map((log) => (
            <details className="recognition-log-item" key={log.id}>
              <summary>
                <input
                  className="log-select-checkbox"
                  type="checkbox"
                  checked={selectedLogIds.includes(log.id)}
                  aria-label={`选择日志 ${log.traceId ?? log.id}`}
                  onClick={(event) => event.stopPropagation()}
                  onChange={() => onToggleLog(log.id)}
                />
                <span className="log-sequence">#{log.sequence ?? indexFallback(logs, log.id)}</span>
                {log.traceId && <span className="log-trace-id">{log.traceId}</span>}
                <span className={isHitLog(log.status) ? "log-status good" : "log-status warn"}>{statusLabel(log.status)}</span>
                <strong>{log.best?.productName ?? "没有匹配到模板"}</strong>
                <small>{new Date(log.createdAt).toLocaleString()}</small>
              </summary>
              <div className="log-detail-grid">
                <LogField label="文件" value={log.filename} />
                <LogField label="识别编号" value={log.traceId ?? "--"} />
                <LogField label="识别来源" value={formatFailureText(log.analysisSource)} />
                <LogField label="门禁结论" value={formatFailureText(log.gate.reason)} />
                <LogField label="最终原因" value={formatFailureText(log.matchReason)} />
                <LogField label="品牌门禁" value={log.gate.hasSnowBrand ? "通过" : "未通过"} />
                <LogField label="门禁命中品牌" value={formatList(log.gate.matchedSnowBrands)} />
                <LogField label="竞品/混合图" value={log.gate.hasCompetitorBrand ? "是，建议人工审核" : "否"} />
                <LogField label="竞品命中品牌" value={formatList(log.gate.matchedCompetitorBrands)} />
                <LogField label="底部文字裁剪" value={log.gate.footerCropped ? "已裁掉底部巡检文字" : "未触发"} />
                <LogField label="模型调用" value={formatModelCalls(log.modelCalls)} wide />
                <LogField label="清洗后文字" value={log.gate.cleanedTexts.length ? log.gate.cleanedTexts.join(" / ") : "--"} wide />
                <LogField
                  label="三层筛选"
                  value={`类型 ${log.pipeline.stage1.candidateCount} 个；品牌关键词 ${log.pipeline.stage2.candidateCount} 个；排序 ${log.pipeline.stage3.candidateCount} 个`}
                  wide
                />
              </div>
              {log.best?.templateImageUrl && (
                <div className="log-template-preview">
                  <img src={log.best.templateImageUrl} alt="命中模板图" loading="lazy" />
                  <div>
                    <strong>{log.best.productName}</strong>
                    <span>
                      {log.best.productCode} / {log.best.packageType} / {log.best.view}
                    </span>
                    <span>相似度 {toPercent(Number(log.best.score ?? 0))}</span>
                  </div>
                </div>
              )}
              <div className="log-candidate-table">
                {log.candidates.map((candidate, index) => (
                  <div className="log-candidate-row" key={`${log.id}-${candidate.productCode}-${candidate.view}-${index}`}>
                    <span>{index + 1}</span>
                    <CandidateImage url={candidate.templateImageUrl} label={candidate.productName} />
                    <strong>{candidate.productName}</strong>
                    <span>{candidate.packageType}</span>
                    <span>{toPercent(Number(candidate.score ?? 0))}</span>
                    <small>{candidate.reason}</small>
                  </div>
                ))}
              </div>
            </details>
          ))
        ) : (
          <div className="empty-source">暂无识别日志</div>
        )}
      </div>
    </div>
  );
}

function CandidateImage({ url, label }: { url: string | null; label: string }) {
  if (!url) {
    return <span className="log-candidate-image empty-image">--</span>;
  }
  return (
    <a className="log-candidate-image" href={url} target="_blank" rel="noreferrer" title={`打开候选模板图：${label}`}>
      <img src={url} alt={label || "候选模板图"} loading="lazy" />
    </a>
  );
}

function isHitLog(status: string) {
  return status === "命中" || status === "鍛戒腑";
}

function statusLabel(status: string) {
  if (status === "鍛戒腑") {
    return "命中";
  }
  if (status === "鏈懡涓?" || status.startsWith("鏈")) {
    return "未命中";
  }
  return status;
}

function indexFallback(logs: RecognitionLog[], id: string) {
  return logs.findIndex((item) => item.id === id) + 1;
}

function formatList(values?: string[]) {
  return values?.length ? values.join(" / ") : "--";
}

function formatModelCalls(calls?: RecognitionLog["modelCalls"]) {
  if (!calls?.length) {
    return "--";
  }
  return calls
    .map((call) => {
      const detail = call.rawText ? `（${formatFailureText(call.rawText).slice(0, 120)}` : "";
      return `${call.role || "default"}:${call.model} ${formatModelSource(call.source)} ${call.elapsedMs}ms${detail}`;
    })
    .join(" / ");
}

function formatModelSource(source?: string) {
  if (source === "model_timeout" || source === "qwen_timeout") {
    return "模型超时";
  }
  if (source === "model_error" || source === "qwen_error") {
    return "模型失败";
  }
  if (source === "no_api_key") {
    return "未配置 Key";
  }
  return source || "";
}

function formatFailureText(value?: string) {
  return (value || "--")
    .replaceAll("qwen_timeout_local_fallback", "model_timeout_local_fallback")
    .replaceAll("qwen_error_local_fallback", "model_error_local_fallback")
    .replaceAll("qwen_timeout", "模型超时")
    .replaceAll("qwen_error", "模型失败")
    .replaceAll("model_timeout_local_fallback", "模型超时后本地视觉兜底")
    .replaceAll("model_error_local_fallback", "模型失败后本地视觉兜底")
    .replaceAll("model_timeout", "模型超时")
    .replaceAll("model_error", "模型失败");
}

function LogField({ label, value, wide = false }: { label: string; value: string; wide?: boolean }) {
  return (
    <div className={wide ? "log-field wide" : "log-field"}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
