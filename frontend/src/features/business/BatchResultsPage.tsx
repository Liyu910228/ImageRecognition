import { BatchResultsPanel } from "../recognition/components/BatchResultsPanel";
import type { useRecognitionWorkflow } from "../recognition/hooks/useRecognitionWorkflow";

type Workflow = ReturnType<typeof useRecognitionWorkflow>;

export function BatchResultsPage({ workflow }: { workflow: Workflow }) {
  return (
    <div className="module-page">
      <div className="module-header">
        <div>
          <h2>批量结果</h2>
          <p>查看 Top 候选、批量导出、单条重试和批量重试。</p>
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
