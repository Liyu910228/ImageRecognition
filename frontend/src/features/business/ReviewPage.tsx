import { BatchResultsPanel } from "../recognition/components/BatchResultsPanel";
import type { useRecognitionWorkflow } from "../recognition/hooks/useRecognitionWorkflow";
import { useBatchReview } from "../recognition/hooks/useBatchReview";
import { toPercent } from "../recognition/utils";

type Workflow = ReturnType<typeof useRecognitionWorkflow>;

export function ReviewPage({ workflow }: { workflow: Workflow }) {
  const stats = useBatchReview(workflow.batchResults);

  return (
    <div className="module-page">
      <div className="module-header">
        <div>
          <h2>人工审核</h2>
          <p>对原图和模板图进行人工确认，并统计当前批次正确率。</p>
        </div>
        <div className="review-kpis">
          <span>已审核 {stats.reviewed}/{stats.total}</span>
          <strong>正确率 {stats.reviewed ? toPercent(stats.rate) : "--"}</strong>
        </div>
      </div>
      <BatchResultsPanel
        recognition={workflow.recognition}
        batchResults={workflow.batchResults}
        recognitionState={workflow.recognitionState}
        onBatchRetry={() => void workflow.retryUnsuccessfulBatchResults()}
        onExport={() => void workflow.handleExportBatchResults()}
        onRetryOne={(index) => void workflow.retryBatchResult(index)}
        onReview={workflow.reviewBatchResult}
      />
    </div>
  );
}
