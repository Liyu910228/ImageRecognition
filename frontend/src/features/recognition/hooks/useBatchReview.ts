import { useMemo } from "react";
import type { BatchRecognitionResult } from "../types";
import { reviewStats } from "../workflowHelpers";

export function useBatchReview(batchResults: BatchRecognitionResult[]) {
  return useMemo(() => reviewStats(batchResults), [batchResults]);
}
