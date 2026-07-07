import { useState } from "react";
import {
  clearRecognitionLogs,
  exportRecognitionLogs,
  fetchRecognitionLogs,
  type RecognitionLog,
  type RecognitionLogFilters
} from "../../shared/api/client";
import { downloadBlob } from "../recognition/workflowHelpers";

const defaultLogFilters: RecognitionLogFilters = {
  q: "",
  status: "all",
  snowGate: "all",
  competitor: "all"
};

export function useRecognitionLogs() {
  const [recognitionLogs, setRecognitionLogs] = useState<RecognitionLog[]>([]);
  const [selectedLogIds, setSelectedLogIds] = useState<string[]>([]);
  const [logPage, setLogPage] = useState(1);
  const [logTotal, setLogTotal] = useState(0);
  const [logPageSize, setLogPageSize] = useState(50);
  const [logsMessage, setLogsMessage] = useState("");
  const [logFilters, setLogFilters] = useState<RecognitionLogFilters>(defaultLogFilters);

  async function loadRecognitionLogs(page = logPage, filters = logFilters) {
    try {
      const result = await fetchRecognitionLogs(page, 50, filters);
      setRecognitionLogs(result.logs);
      setLogPage(result.page);
      setLogTotal(result.total);
      setLogPageSize(result.pageSize);
      setLogsMessage("");
    } catch (error) {
      setLogsMessage(error instanceof Error ? error.message : "识别日志请求失败");
    }
  }

  async function handleClearRecognitionLogs() {
    setLogsMessage("正在清空...");
    try {
      await clearRecognitionLogs();
      setRecognitionLogs([]);
      setSelectedLogIds([]);
      setLogPage(1);
      setLogTotal(0);
      setLogsMessage("识别日志已清空");
    } catch (error) {
      setLogsMessage(error instanceof Error ? error.message : "识别日志清空失败");
    }
  }

  function updateLogFilters(nextFilters: RecognitionLogFilters) {
    setLogFilters(nextFilters);
    setSelectedLogIds([]);
    void loadRecognitionLogs(1, nextFilters);
  }

  function toggleLogSelection(id: string) {
    setSelectedLogIds((current) => (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]));
  }

  function selectCurrentPageLogs() {
    setSelectedLogIds((current) => Array.from(new Set([...current, ...recognitionLogs.map((log) => log.id)])));
  }

  function clearSelectedLogs() {
    setSelectedLogIds([]);
  }

  async function handleExportRecognitionLogs() {
    setLogsMessage("正在导出全部日志...");
    try {
      const blob = await exportRecognitionLogs(logFilters);
      downloadBlob(blob, `识别日志-全部-${new Date().toISOString().slice(0, 10)}.xlsx`);
      setLogsMessage("全部识别日志已导出");
    } catch (error) {
      setLogsMessage(error instanceof Error ? error.message : "识别日志导出失败");
    }
  }

  async function handleExportSelectedRecognitionLogs() {
    if (!selectedLogIds.length) {
      setLogsMessage("请先勾选要导出的日志");
      return;
    }
    setLogsMessage(`正在导出选中的 ${selectedLogIds.length} 条日志...`);
    try {
      const blob = await exportRecognitionLogs(logFilters, selectedLogIds);
      downloadBlob(blob, `识别日志-选中-${new Date().toISOString().slice(0, 10)}.xlsx`);
      setLogsMessage(`已导出选中的 ${selectedLogIds.length} 条日志`);
    } catch (error) {
      setLogsMessage(error instanceof Error ? error.message : "选中日志导出失败");
    }
  }

  return {
    recognitionLogs,
    selectedLogIds,
    logPage,
    logTotal,
    logPageSize,
    logsMessage,
    logFilters,
    loadRecognitionLogs,
    handleClearRecognitionLogs,
    handleExportRecognitionLogs,
    handleExportSelectedRecognitionLogs,
    updateLogFilters,
    toggleLogSelection,
    selectCurrentPageLogs,
    clearSelectedLogs
  };
}
