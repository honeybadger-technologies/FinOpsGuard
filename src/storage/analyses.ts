export interface AnalysisRecord {
  request_id: string;
  started_at: string; // ISO
  duration_ms: number;
  summary: string;
}

const analyses: AnalysisRecord[] = [];

export function addAnalysis(record: AnalysisRecord): void {
  analyses.unshift(record);
  if (analyses.length > 1000) analyses.pop();
}

export function listAnalyses(limit = 20, after?: string): { items: AnalysisRecord[]; next_cursor?: string } {
  let startIdx = 0;
  if (after) {
    const idx = analyses.findIndex((a) => a.started_at < after);
    startIdx = idx >= 0 ? idx : analyses.length;
  }
  const items = analyses.slice(startIdx, startIdx + limit);
  const next = startIdx + limit < analyses.length ? analyses[startIdx + limit - 1].started_at : undefined;
  return { items, next_cursor: next };
}


