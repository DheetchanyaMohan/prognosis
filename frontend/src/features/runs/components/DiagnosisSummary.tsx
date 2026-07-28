import { StatCard } from "@/components/ui"
import { toUtcDate } from "@/lib/format-date"
import { computeTotalDurationMs, formatDurationMs } from "../utils/agent-workflow"
import type { DiagnosisResponse } from "../types"

interface DiagnosisSummaryProps {
  data: DiagnosisResponse
}

/**
 * The executive summary a reader should absorb before the details
 * below (Milestone 6 §1). "AI Model" and "Workflow Engine" are static
 * facts about this deployment (Gemini 3.6 Flash via LangGraph) — they
 * are NOT fields in `DiagnosisResponse` and don't vary per request,
 * so they're not "derived from the response" the way every other
 * value here is; they're included because they're real and relevant,
 * not fabricated. Every other stat is either a direct field or a
 * plain computation over real response data (execution time is
 * derived from the first/last real trace timestamps).
 */
export function DiagnosisSummary({ data }: DiagnosisSummaryProps) {
  const totalDurationMs = computeTotalDurationMs(data.trace)
  const groundedCount = data.recommendations.filter((rec) => rec.is_grounded).length

  return (
    <div className="flex flex-col gap-3">
      <h3 className="text-sm font-medium text-foreground">Diagnosis Summary</h3>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard label="AI Model" value="Gemini 3.6 Flash" />
        <StatCard label="Workflow Engine" value="LangGraph" />
        <StatCard label="Generated" value={toUtcDate(data.generated_at).toLocaleTimeString()} />
        <StatCard
          label="Execution Time"
          value={totalDurationMs !== null ? formatDurationMs(totalDurationMs) : "—"}
        />
        <StatCard label="Knowledge Chunks" value={data.retrieved_knowledge.length} />
        <StatCard label="Similar Runs" value={data.similar_runs.length} />
        <StatCard label="Hypotheses" value={data.hypotheses.length} />
        <StatCard label="Grounded Recs" value={`${groundedCount}/${data.recommendations.length}`} />
      </div>
    </div>
  )
}