import type { RecognitionResponse } from "../../shared/api/client";
import type { BatchRecognitionResult } from "./types";

export function batchStatusLabel(result: BatchRecognitionResult) {
  if (result.status === "success") {
    return "完成";
  }
  if (result.status === "no_match") {
    return "未命中";
  }
  if (result.status === "retrying") {
    return "重试中";
  }
  return "失败";
}

export function statusFromResponse(response: RecognitionResponse): BatchRecognitionResult["status"] {
  return response.best ? "success" : "no_match";
}

export function toPercent(score: number) {
  return `${Math.round(score * 1000) / 10}%`;
}
