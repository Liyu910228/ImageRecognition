import { useEffect, useState } from "react";
import {
  exportBatchResults,
  extractWorkbookImageLinks,
  recognizeImage,
  recognizeImageUrl,
  type RecognitionResponse,
  type WorkbookImageLink
} from "../../../shared/api/client";
import type { BatchRecognitionResult } from "../types";
import { batchStatusLabel, statusFromResponse } from "../utils";
import { createBatchId, createTraceId, downloadBlob, isSupportedImageFile } from "../workflowHelpers";

export type RecognitionState = "idle" | "recognizing" | "success" | "error";

export function useRecognitionWorkflow(frontendApiKey: string) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [folderFiles, setFolderFiles] = useState<File[]>([]);
  const [workbookLinks, setWorkbookLinks] = useState<WorkbookImageLink[]>([]);
  const [workbookName, setWorkbookName] = useState("");
  const [batchResults, setBatchResults] = useState<BatchRecognitionResult[]>([]);
  const [batchProgress, setBatchProgress] = useState({ current: 0, total: 0 });
  const [imageUrl, setImageUrl] = useState("");
  const [manualHints, setManualHints] = useState("");
  const [previewUrl, setPreviewUrl] = useState("");
  const [recognitionState, setRecognitionState] = useState<RecognitionState>("idle");
  const [recognitionError, setRecognitionError] = useState("");
  const [recognition, setRecognition] = useState<RecognitionResponse | null>(null);

  useEffect(() => {
    if (!selectedFile) {
      setPreviewUrl((current) => (current.startsWith("blob:") ? "" : current));
      return;
    }
    const objectUrl = URL.createObjectURL(selectedFile);
    setPreviewUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [selectedFile]);

  function resetBatchState() {
    setBatchResults([]);
    setBatchProgress({ current: 0, total: 0 });
  }

  async function handleFileChange(file: File | undefined) {
    if (!file) {
      return;
    }
    setSelectedFile(file);
    setFolderFiles([]);
    setWorkbookLinks([]);
    setWorkbookName("");
    resetBatchState();
    setRecognition(null);
    setRecognitionError("");
    setRecognitionState("idle");
  }

  async function handleFolderChange(files: FileList | null) {
    const images = Array.from(files ?? [])
      .filter(isSupportedImageFile)
      .sort((a, b) => (a.webkitRelativePath || a.name).localeCompare(b.webkitRelativePath || b.name));
    if (!images.length) {
      setRecognitionError("文件夹里没有可识别的 JPG、PNG 或 WebP 图片");
      setRecognitionState("error");
      return;
    }
    setFolderFiles(images);
    setWorkbookLinks([]);
    setWorkbookName("");
    setSelectedFile(images[0]);
    setRecognition(null);
    setBatchResults([]);
    setBatchProgress({ current: 0, total: images.length });
    setRecognitionError("");
    setRecognitionState("idle");
  }

  async function handleWorkbookLinkUpload(file: File | undefined) {
    if (!file) {
      return;
    }
    setSelectedFile(null);
    setFolderFiles([]);
    setRecognition(null);
    resetBatchState();
    setRecognitionState("recognizing");
    setRecognitionError("");
    try {
      const result = await extractWorkbookImageLinks(file);
      setWorkbookLinks(result.links);
      setWorkbookName(result.filename);
      setRecognitionState("idle");
    } catch (error) {
      setWorkbookLinks([]);
      setWorkbookName("");
      setRecognitionError(error instanceof Error ? error.message : "表格链接读取失败");
      setRecognitionState("error");
    }
  }

  async function recognizeWorkbookLinks() {
    setSelectedFile(null);
    setPreviewUrl("");
    setRecognitionState("recognizing");
    setRecognitionError("");
    setBatchResults([]);
    setBatchProgress({ current: 0, total: workbookLinks.length });
    const nextResults: BatchRecognitionResult[] = [];
    const batchId = createBatchId();
    for (const [index, item] of workbookLinks.entries()) {
      const traceId = createTraceId(batchId, index);
      setImageUrl(item.image_url);
      setPreviewUrl(item.image_url);
      setBatchProgress({ current: index + 1, total: workbookLinks.length });
      try {
        const response = await recognizeImageUrl(item.image_url, manualHints, frontendApiKey, traceId);
        setRecognition(response);
        nextResults.push({
          filename: item.image_url,
          processIndex: index + 1,
          traceId,
          status: statusFromResponse(response),
          sourceType: "url",
          sourceUrl: item.image_url,
          response,
          row: item.row,
          sheet: item.sheet
        });
      } catch (error) {
        nextResults.push({
          filename: item.image_url,
          processIndex: index + 1,
          traceId,
          status: "error",
          sourceType: "url",
          sourceUrl: item.image_url,
          row: item.row,
          sheet: item.sheet,
          error: error instanceof Error ? error.message : "图片链接识别失败"
        });
      }
      setBatchResults([...nextResults]);
    }
    finishBatch(nextResults, "表格链接批量识别完成");
  }

  async function recognizeFolderFiles() {
    setRecognitionState("recognizing");
    setRecognitionError("");
    setBatchResults([]);
    setBatchProgress({ current: 0, total: folderFiles.length });
    const nextResults: BatchRecognitionResult[] = [];
    const batchId = createBatchId();
    for (const [index, file] of folderFiles.entries()) {
      const traceId = createTraceId(batchId, index);
      setSelectedFile(file);
      setBatchProgress({ current: index + 1, total: folderFiles.length });
      try {
        const response = await recognizeImage(file, manualHints, frontendApiKey, traceId);
        setRecognition(response);
        nextResults.push({
          filename: file.webkitRelativePath || file.name,
          processIndex: index + 1,
          traceId,
          status: statusFromResponse(response),
          sourceType: "file",
          sourceFile: file,
          response
        });
      } catch (error) {
        nextResults.push({
          filename: file.webkitRelativePath || file.name,
          processIndex: index + 1,
          traceId,
          status: "error",
          sourceType: "file",
          sourceFile: file,
          error: error instanceof Error ? error.message : "识别失败"
        });
      }
      setBatchResults([...nextResults]);
    }
    finishBatch(nextResults, "批量识别完成");
  }

  function finishBatch(results: BatchRecognitionResult[], prefix: string) {
    const failedCount = results.filter((result) => result.status === "error").length;
    const noMatchCount = results.filter((result) => result.status === "no_match").length;
    if (failedCount || noMatchCount) {
      setRecognitionError(`${prefix}，${failedCount} 条失败，${noMatchCount} 条未命中`);
      setRecognitionState("error");
    } else {
      setRecognitionState("success");
    }
  }

  async function handleRecognize() {
    if (workbookLinks.length) {
      await recognizeWorkbookLinks();
      return;
    }
    if (folderFiles.length) {
      await recognizeFolderFiles();
      return;
    }
    if (!selectedFile) {
      setRecognitionError("请先选择一张图片");
      setRecognitionState("error");
      return;
    }
    setRecognitionState("recognizing");
    setRecognitionError("");
    try {
      setRecognition(await recognizeImage(selectedFile, manualHints, frontendApiKey, createTraceId(createBatchId(), 0)));
      setRecognitionState("success");
    } catch (error) {
      setRecognitionError(error instanceof Error ? error.message : "识别失败");
      setRecognitionState("error");
    }
  }

  async function handleRecognizeUrl() {
    const nextUrl = imageUrl.trim();
    if (!nextUrl) {
      setRecognitionError("请先输入图片链接");
      setRecognitionState("error");
      return;
    }
    setSelectedFile(null);
    setFolderFiles([]);
    setWorkbookLinks([]);
    setWorkbookName("");
    resetBatchState();
    setPreviewUrl(nextUrl);
    setRecognitionState("recognizing");
    setRecognitionError("");
    try {
      setRecognition(await recognizeImageUrl(nextUrl, manualHints, frontendApiKey, createTraceId(createBatchId(), 0)));
      setRecognitionState("success");
    } catch (error) {
      setRecognitionError(error instanceof Error ? error.message : "图片链接识别失败");
      setRecognitionState("error");
    }
  }

  async function handleExportBatchResults() {
    if (!batchResults.length) {
      setRecognitionError("暂无可导出的批量识别结果");
      setRecognitionState("error");
      return;
    }
    setRecognitionError("");
    try {
      const blob = await exportBatchResults(
        batchResults.map((result) => ({
          trace_id: result.traceId ?? "",
          source: result.filename,
          status: batchStatusLabel(result),
          product_code: result.response?.best?.product_code ?? "",
          product_name: result.response?.best?.product_name ?? "",
          package_type: result.response?.best?.package_type ?? "",
          score: result.response?.best?.score ?? null,
          sheet: result.sheet ?? "",
          row: result.row ?? null,
          error: result.error ?? (result.status === "no_match" ? "没有匹配到模板候选" : "")
        }))
      );
      downloadBlob(blob, `批量识别结果-${new Date().toISOString().slice(0, 10)}.xlsx`);
    } catch (error) {
      setRecognitionError(error instanceof Error ? error.message : "批量结果导出失败");
      setRecognitionState("error");
    }
  }

  function reviewBatchResult(index: number, reviewStatus: BatchRecognitionResult["reviewStatus"]) {
    setBatchResults((current) =>
      current.map((item, itemIndex) => (itemIndex === index ? { ...item, reviewStatus } : item))
    );
  }

  async function retryBatchResult(index: number): Promise<BatchRecognitionResult["status"] | null> {
    const target = batchResults[index];
    if (!target || target.status === "retrying") {
      return null;
    }
    setRecognitionError("");
    setBatchResults((current) =>
      current.map((item, itemIndex) =>
        itemIndex === index ? { ...item, status: "retrying", error: "", response: undefined, reviewStatus: undefined } : item
      )
    );
    try {
      const response =
        target.sourceType === "url"
          ? await recognizeImageUrl(target.sourceUrl ?? target.filename, manualHints, frontendApiKey, target.traceId ?? "")
          : target.sourceFile
            ? await recognizeImage(target.sourceFile, manualHints, frontendApiKey, target.traceId ?? "")
            : await Promise.reject(new Error("原始图片文件不存在，请重新选择文件夹后再试"));
      setRecognition(response);
      const nextStatus = statusFromResponse(response);
      setBatchResults((current) =>
        current.map((item, itemIndex) =>
          itemIndex === index
            ? {
                ...target,
                status: nextStatus,
                response,
                error: "",
                reviewStatus: undefined
              }
            : item
        )
      );
      return nextStatus;
    } catch (error) {
      setBatchResults((current) =>
        current.map((item, itemIndex) =>
          itemIndex === index
            ? {
                ...target,
                status: "error",
                response: undefined,
                error: error instanceof Error ? error.message : "重试失败",
                reviewStatus: undefined
              }
            : item
        )
      );
      return "error";
    }
  }

  async function retryUnsuccessfulBatchResults() {
    const indexes = batchResults
      .map((result, index) => ({ result, index }))
      .filter(({ result }) => result.status === "error" || result.status === "no_match")
      .map(({ index }) => index);
    if (!indexes.length) {
      setRecognitionError("没有需要重试的失败或未命中记录");
      setRecognitionState("error");
      return;
    }
    setRecognitionState("recognizing");
    setRecognitionError("");
    setBatchProgress({ current: 0, total: indexes.length });
    let failedCount = 0;
    let noMatchCount = 0;
    for (const [progressIndex, resultIndex] of indexes.entries()) {
      setBatchProgress({ current: progressIndex + 1, total: indexes.length });
      const status = await retryBatchResult(resultIndex);
      if (status === "error") {
        failedCount += 1;
      }
      if (status === "no_match") {
        noMatchCount += 1;
      }
    }
    if (failedCount || noMatchCount) {
      setRecognitionError(`批量重试完成，仍有 ${failedCount} 条失败，${noMatchCount} 条未命中`);
      setRecognitionState("error");
    } else {
      setRecognitionState("success");
    }
  }

  return {
    selectedFile,
    folderFiles,
    workbookLinks,
    workbookName,
    batchResults,
    batchProgress,
    imageUrl,
    manualHints,
    previewUrl,
    recognitionState,
    recognitionError,
    recognition,
    setImageUrl,
    setManualHints,
    handleFileChange,
    handleFolderChange,
    handleWorkbookLinkUpload,
    handleRecognize,
    handleRecognizeUrl,
    handleExportBatchResults,
    retryBatchResult,
    retryUnsuccessfulBatchResults,
    reviewBatchResult
  };
}
