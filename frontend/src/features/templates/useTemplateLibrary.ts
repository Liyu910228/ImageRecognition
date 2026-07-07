import { useState } from "react";
import {
  deleteTemplateSource,
  fetchTemplateSources,
  getTemplateSourceDownloadUrl,
  uploadTemplateWorkbooks,
  type TemplateSource
} from "../../shared/api/client";

export type TemplateUploadState = "idle" | "uploading" | "success" | "error";

export function useTemplateLibrary(onStatusChanged?: () => Promise<void> | void) {
  const [templateUploadState, setTemplateUploadState] = useState<TemplateUploadState>("idle");
  const [templateUploadMessage, setTemplateUploadMessage] = useState("");
  const [templateSources, setTemplateSources] = useState<TemplateSource[]>([]);

  async function loadTemplateSources() {
    const result = await fetchTemplateSources();
    setTemplateSources(result.sources);
  }

  async function handleTemplateUpload(files: FileList | null) {
    const selected = Array.from(files ?? []);
    if (!selected.length) {
      return;
    }
    setTemplateUploadState("uploading");
    setTemplateUploadMessage("正在上传并重建模板库，这可能需要一些时间...");
    try {
      const result = await uploadTemplateWorkbooks(selected);
      setTemplateUploadState("success");
      setTemplateUploadMessage(`已导入 ${result.uploadedFiles.length} 个文件，${result.productCount} 个产品，${result.indexedImageCount} 张模板图已构建完成`);
      setTemplateSources(result.sources);
      await onStatusChanged?.();
    } catch (error) {
      setTemplateUploadState("error");
      setTemplateUploadMessage(error instanceof Error ? error.message : "模板库上传失败");
    }
  }

  async function handleDeleteTemplateSource(filename: string) {
    setTemplateUploadState("uploading");
    setTemplateUploadMessage(`正在删除 ${filename} 并重建模板库...`);
    try {
      const result = await deleteTemplateSource(filename);
      setTemplateSources(result.sources);
      setTemplateUploadState("success");
      setTemplateUploadMessage(`已删除 ${result.deletedFile}，当前 ${result.productCount} 个产品，${result.indexedImageCount} 张模板图已构建完成`);
      await onStatusChanged?.();
    } catch (error) {
      setTemplateUploadState("error");
      setTemplateUploadMessage(error instanceof Error ? error.message : "模板源文件删除失败");
    }
  }

  function handleDownloadTemplateSource(filename: string) {
    setTemplateUploadState("success");
    setTemplateUploadMessage(`已开始下载 ${filename}；大文件会在浏览器下载列表中继续传输`);

    const link = document.createElement("a");
    link.href = getTemplateSourceDownloadUrl(filename);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
  }

  return {
    templateUploadState,
    templateUploadMessage,
    templateSources,
    loadTemplateSources,
    handleTemplateUpload,
    handleDeleteTemplateSource,
    handleDownloadTemplateSource
  };
}
