import type { BatchRecognitionResult } from "./types";

export const folderPickerProps = {
  directory: "",
  webkitdirectory: ""
} as Record<string, string>;

export function isSupportedImageFile(file: File) {
  const suffix = file.name.toLowerCase().split(".").pop() ?? "";
  return file.type.startsWith("image/") || ["jpg", "jpeg", "png", "webp"].includes(suffix);
}

export function downloadBlob(blob: Blob, filename: string) {
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(objectUrl);
}

export function createBatchId() {
  const timestamp = new Date()
    .toISOString()
    .replace(/\D/g, "")
    .slice(0, 14);
  const suffix = Math.random().toString(36).slice(2, 6).toUpperCase();
  return `B${timestamp}-${suffix}`;
}

export function createTraceId(batchId: string, index: number) {
  return `${batchId}-${String(index + 1).padStart(3, "0")}`;
}

export function reviewStats(batchResults: BatchRecognitionResult[]) {
  const reviewed = batchResults.filter((result) => result.reviewStatus);
  const correct = reviewed.filter((result) => result.reviewStatus === "correct").length;
  return {
    reviewed: reviewed.length,
    correct,
    total: batchResults.length,
    rate: reviewed.length ? correct / reviewed.length : 0
  };
}
