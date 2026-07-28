import { computeStageDurations, computeTotalDurationMs, formatDurationMs } from "../utils/agent-workflow"
import type { TraceEntry } from "../types"

interface WorkflowPerformanceSummaryProps {
  trace: TraceEntry[]
}

/**
 * Every duration here is derived from real, consecutive trace
 * timestamps (Milestone 6 §2) — nothing is fabricated. Bar widths are
 * proportional to the largest real duration in this trace (a plain
 * linear scale, not exaggerated); the last stage always shows "—"
 * rather than a fabricated 0, since there's no subsequent timestamp
 * to measure its duration against.
 */
export function WorkflowPerformanceSummary({ trace }: WorkflowPerformanceSummaryProps) {
  if (trace.length === 0) {
    return null
  }

  const stages = computeStageDurations(trace)
  const totalMs = computeTotalDurationMs(trace)
  const maxMs = Math.max(...stages.map((stage) => stage.durationMs ?? 0), 1)

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-sm font-medium text-foreground">Workflow Performance</h3>
        <span className="font-mono text-xs tabular-nums text-muted-foreground">
          {totalMs !== null ? `Total ${formatDurationMs(totalMs)}` : "Total —"}
        </span>
      </div>
      <div className="flex flex-col gap-1.5">
        {stages.map((stage, index) => (
          <div key={`${stage.label}-${index}`} className="flex items-center gap-2 text-xs">
            <span className="w-36 shrink-0 truncate text-muted-foreground">
              {index + 1}. {stage.label}
            </span>
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-secondary">
              {stage.durationMs !== null && (
                <div
                  className="h-full rounded-full bg-foreground/40"
                  style={{ width: `${Math.max((stage.durationMs / maxMs) * 100, 4)}%` }}
                />
              )}
            </div>
            <span className="w-12 shrink-0 text-right font-mono tabular-nums text-muted-foreground">
              {stage.durationMs !== null ? formatDurationMs(stage.durationMs) : "—"}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}