import { useRunQuery, deriveRunStatus, StatusBadge, formatLoss } from "@/features/runs"
import type { RetrievedChunk } from "../types"

interface SimilarRunCardProps {
  chunk: RetrievedChunk
}

interface SimilarRunLiveStatsProps {
  runId: string
}

/**
 * Real run status and validation performance, fetched via the exact
 * same `useRunQuery` (and cache) every other run view in the app
 * already uses — not a new data source, and not fabricated. If the
 * run's own diagnostics/summary haven't finished yet, this simply
 * reflects that honestly (StatusBadge shows "pending", val loss is
 * omitted) rather than inventing a placeholder number.
 */
function SimilarRunLiveStats({ runId }: SimilarRunLiveStatsProps) {
  const { data, isPending } = useRunQuery(runId)

  if (isPending) {
    return <span className="text-xs text-muted-foreground">Loading run status…</span>
  }
  if (!data) {
    return null
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <StatusBadge flags={deriveRunStatus(data.diagnostics)} />
      {data.summary && (
        <span className="font-mono text-xs tabular-nums text-muted-foreground">
          val loss {formatLoss(data.summary.best_val_loss)}
        </span>
      )}
    </div>
  )
}

/**
 * Milestone 6 §4: similarity score, real run status, and real
 * validation performance lead the card; the longer natural-language
 * summary (`chunk.text`) — the "why considered relevant" explanation
 * — comes last, not first. `metadata.run_id` is only present for
 * run_summary chunks (Integration Guide), so the live-stats row is
 * conditionally rendered rather than assumed.
 */
export function SimilarRunCard({ chunk }: SimilarRunCardProps) {
  const runId = chunk.metadata.run_id

  return (
    <div className="border-b border-border pb-3 last:border-0 last:pb-0">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="font-mono text-xs tabular-nums text-muted-foreground">
          similarity {chunk.score.toFixed(2)}
        </span>
        {runId && <span className="font-mono text-xs text-muted-foreground">{runId}</span>}
      </div>
      {runId && (
        <div className="mt-1.5">
          <SimilarRunLiveStats runId={runId} />
        </div>
      )}
      <p className="mt-1.5 text-sm text-foreground">{chunk.text}</p>
    </div>
  )
}