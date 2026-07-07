import { RecognitionLogsPanel } from "../settings/RecognitionLogsPanel";
import type { useRecognitionLogs } from "../settings/useRecognitionLogs";

type LogsState = ReturnType<typeof useRecognitionLogs>;

export function LogsPage({ logs }: { logs: LogsState }) {
  return (
    <div className="module-page">
      <div className="module-header">
        <div>
          <h2>日志管理</h2>
          <p>筛选、查找和分页查看图片匹配过程。</p>
        </div>
      </div>
      <RecognitionLogsPanel
        logs={logs.recognitionLogs}
        selectedLogIds={logs.selectedLogIds}
        page={logs.logPage}
        pageSize={logs.logPageSize}
        total={logs.logTotal}
        filters={logs.logFilters}
        logsMessage={logs.logsMessage}
        onRefresh={() => void logs.loadRecognitionLogs(logs.logPage)}
        onPageChange={(page) => void logs.loadRecognitionLogs(page)}
        onFiltersChange={logs.updateLogFilters}
        onClear={() => void logs.handleClearRecognitionLogs()}
        onExportAll={() => void logs.handleExportRecognitionLogs()}
        onExportSelected={() => void logs.handleExportSelectedRecognitionLogs()}
        onToggleLog={logs.toggleLogSelection}
        onSelectPage={logs.selectCurrentPageLogs}
        onClearSelected={logs.clearSelectedLogs}
      />
    </div>
  );
}
