import { Link } from "react-router-dom"
import { useRunQuery, deriveRunStatus, StatusBadge, formatLoss } from "@/features/runs"
import { Skeleton } from "@/components/ui"
import { cn, focusRingClass } from "@/lib/utils"

interface RunRowProps {
  experimentId: string
  runId: string
}

/**
 * One row per `run_id` (Architecture §7/§8). Initially renders with
 * just the ID — already known from `experiment.run_ids`, so it never
 * appears to load — and a small loading indicator, then upgrades in
 * place once its own `GET /api/v1/runs/{id}` resolves. Deliberately
 * NOT optimized into a single batched request: this is the documented
 * N+1 pattern (Integration Guide §7/§9), real and currently
 * unavoidable.
 *
 * The whole row is a keyboard-operable `Link` (Accessibility §17),
 * matching the same pattern `ExperimentCard` already uses rather than
 * a click-only div.
 */
export function RunRow({ experimentId, runId }: RunRowProps) {
  const { data, isPending, isError } = useRunQuery(runId)

  return (
    <Link
      to={`/experiments/${encodeURIComponent(experimentId)}/runs/${encodeURIComponent(runId)}`}
      className={cn(
        "flex items-center justify-between gap-4 rounded-md border border-border px-4 py-3 text-sm transition-colors hover:border-foreground/20",
        focusRingClass,
      )}
    >
      <span className="font-mono text-foreground">{runId}</span>

      <div className="flex items-center gap-3">
        {isPending && (
          <>
            <Skeleton className="h-5 w-16 rounded-full" />
            <Skeleton className="h-4 w-20" />
          </>
        )}

        {isError && <span className="text-xs text-muted-foreground">Unavailable</span>}

        {data && (
          <>
            <StatusBadge flags={deriveRunStatus(data.diagnostics)} />
            <span className="font-mono text-xs tabular-nums text-muted-foreground">
              {data.summary ? `val loss ${formatLoss(data.summary.best_val_loss)}` : "pending"}
            </span>
          </>
        )}
      </div>
    </Link>
  )
}
