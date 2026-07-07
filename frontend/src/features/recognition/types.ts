import type { RecognitionResponse } from "../../shared/api/client";

export type BatchRecognitionResult = {
  filename: string;
  processIndex?: number;
  traceId?: string;
  status: "success" | "no_match" | "error" | "retrying";
  reviewStatus?: "correct" | "wrong";
  sourceType: "file" | "url";
  sourceFile?: File;
  sourceUrl?: string;
  response?: RecognitionResponse;
  error?: string;
  row?: number;
  sheet?: string;
};
