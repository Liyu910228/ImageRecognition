import { useEffect, useMemo, useState } from "react";
import { Check, Download, RefreshCw, X } from "lucide-react";
import type { RecognitionResponse } from "../../../shared/api/client";
import type { BatchRecognitionResult } from "../types";
import { batchStatusLabel, toPercent } from "../utils";

export function BatchResultsPanel({
  recognition,
  batchResults,
  recognitionState,
  onBatchRetry,
  onExport,
  onRetryOne,
  onReview
}: {
  recognition: RecognitionResponse | null;
  batchResults: BatchRecognitionResult[];
  recognitionState: string;
  onBatchRetry: () => void;
  onExport: () => void;
  onRetryOne: (index: number) => void;
  onReview: (index: number, status: BatchRecognitionResult["reviewStatus"]) => void;
}) {
  const reviewStats = useMemo(() => {
    const reviewed = batchResults.filter((result) => result.reviewStatus);
    const correct = reviewed.filter((result) => result.reviewStatus === "correct").length;
    return {
      reviewed: reviewed.length,
      correct,
      rate: reviewed.length ? correct / reviewed.length : 0
    };
  }, [batchResults]);

  return (
    <section className="lower-grid single-column">
      <div className="panel">
        <div className="panel-heading">
          <div>
            <h2>Top 5 候选</h2>
            <p>候选列表会在识别完成后出现，模板图可点击放大比对</p>
          </div>
          {batchResults.length > 0 && (
            <div className="table-actions">
              <div className="review-summary">
                <span>已审核 {reviewStats.reviewed}/{batchResults.length}</span>
                <strong>正确率 {reviewStats.reviewed ? toPercent(reviewStats.rate) : "--"}</strong>
              </div>
              <button className="secondary-action" type="button" onClick={onBatchRetry} disabled={recognitionState === "recognizing"}>
                <RefreshCw size={18} />
                批量重试
              </button>
              <button className="secondary-action" type="button" onClick={onExport}>
                <Download size={18} />
                导出Excel
              </button>
            </div>
          )}
        </div>
        {recognition?.candidates.length ? (
          <div className="candidate-table">
            <div className="candidate-row table-head">
              <span>排名</span>
              <span>模板图</span>
              <span>产品编码</span>
              <span>产品名称</span>
              <span>类型</span>
              <span>视角</span>
              <span>相似度</span>
            </div>
            {recognition.candidates.map((candidate, index) => (
              <div className="candidate-row" key={`${candidate.image_path}-${index}`}>
                <span>{index + 1}</span>
                <ImageCell url={candidate.template_image_url ?? undefined} label={`候选模板图 ${index + 1}`} />
                <span>{candidate.product_code}</span>
                <span>{candidate.product_name}</span>
                <span>{candidate.package_type}</span>
                <span>{candidate.view}</span>
                <strong title={`视觉 ${toPercent(candidate.visual_score)} / 品牌 ${toPercent(candidate.brand_score ?? 0)} / 文本 ${toPercent(candidate.text_score)}`}>
                  {toPercent(candidate.score)}
                </strong>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-table">暂无识别结果</div>
        )}
        {batchResults.length > 0 && (
          <div className="batch-table">
            <div className="batch-row table-head">
              <span>处理序号</span>
              <span>识别编号</span>
              <span>原图</span>
              <span>模板图</span>
              <span>状态</span>
              <span>产品编码</span>
              <span>产品名称</span>
              <span>瓶/听/箱</span>
              <span>相似度</span>
              <span>人工审核</span>
              <span>操作</span>
            </div>
            {batchResults.map((result, index) => (
              <div className="batch-row" key={`${result.filename}-${result.sheet ?? ""}-${result.row ?? ""}`}>
                <span className="process-index">#{result.processIndex ?? index + 1}</span>
                <span className="trace-id" title={result.traceId ?? ""}>{result.traceId ?? "--"}</span>
                <ImageCell file={result.sourceFile} url={result.sourceUrl} label="原图" />
                <ImageCell url={result.response?.best?.template_image_url ?? undefined} label="模板图" />
                <span>{batchStatusLabel(result)}</span>
                <span>{result.response?.best?.product_code ?? "--"}</span>
                <span>{result.response?.best?.product_name ?? result.error ?? "没有匹配到模板候选"}</span>
                <span>{result.response?.best?.package_type ?? "--"}</span>
                <strong>{result.response?.best ? toPercent(result.response.best.score) : "--"}</strong>
                <div className="review-actions">
                  <button
                    className={result.reviewStatus === "correct" ? "icon-action active-good" : "icon-action"}
                    type="button"
                    title="人工审核正确"
                    disabled={!result.response?.best}
                    onClick={() => onReview(index, result.reviewStatus === "correct" ? undefined : "correct")}
                  >
                    <Check size={16} />
                  </button>
                  <button
                    className={result.reviewStatus === "wrong" ? "icon-action active-bad" : "icon-action"}
                    type="button"
                    title="人工审核错误"
                    disabled={!result.response?.best}
                    onClick={() => onReview(index, result.reviewStatus === "wrong" ? undefined : "wrong")}
                  >
                    <X size={16} />
                  </button>
                </div>
                <button
                  className="text-action"
                  type="button"
                  disabled={result.status === "retrying" || recognitionState === "recognizing"}
                  onClick={() => onRetryOne(index)}
                >
                  重试
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

function ImageCell({ file, url, label }: { file?: File; url?: string; label: string }) {
  const [objectUrl, setObjectUrl] = useState("");

  useEffect(() => {
    if (!file) {
      setObjectUrl("");
      return;
    }
    const nextUrl = URL.createObjectURL(file);
    setObjectUrl(nextUrl);
    return () => URL.revokeObjectURL(nextUrl);
  }, [file]);

  const src = url || objectUrl;
  if (!src) {
    return <span className="image-cell empty-image">--</span>;
  }
  return (
    <a className="image-cell" href={src} target="_blank" rel="noreferrer" title={`打开${label}`}>
      <img src={src} alt={label} loading="lazy" />
    </a>
  );
}
