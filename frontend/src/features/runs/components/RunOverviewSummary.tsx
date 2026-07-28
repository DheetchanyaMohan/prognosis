import { PendingCard, Badge } from "@/components/ui"
import { AlertTriangle } from "lucide-react"
import type { RunSummaryResponse } from "../types"

interface RunOverviewSummaryProps {
  summary: RunSummaryResponse | null
  isPolling: boolean
}

/**
 * The compact "what happened" blurb for the new Overview section —
 * `summary.description` (already full-sentence prose from the
 * backend, safe to render directly) plus a `diverged` warning badge
 * when true. Deliberately excludes the numeric stat grid, which now
 * lives in `SummaryPanel` under the Metrics section — Overview needs
 * to stay short enough that "AI Diagnosis" (section 2) is reachable
 * without scrolling.
 */
export function RunOverviewSummary({ summary, isPolling }: RunOverviewSummaryProps) {
  if (!summary) {
    return (
      <PendingCard
        title="Training in progress"
        message="A summary will appear once this run finishes."
        polling={isPolling}
      />
    )
  }

  return (
    <div className="flex flex-wrap items-start justify-between gap-3">
      <p className="max-w-2xl text-sm text-foreground">{summary.description}</p>
      {summary.diverged && (
        <Badge tone="concern" icon={<AlertTriangle className="size-3.5" aria-hidden="true" />}>
          Diverged early
        </Badge>
      )}
    </div>
  )
}