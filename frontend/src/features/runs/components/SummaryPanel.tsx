import { PendingCard, Badge, StatCard } from "@/components/ui"
import { AlertTriangle } from "lucide-react"
import { formatWallClock, formatLoss, formatPercent } from "../utils/format-run-stats"
import type { RunSummaryResponse } from "../types"

interface SummaryPanelProps {
  summary: RunSummaryResponse | null
  isPolling: boolean
}

/**
 * Architecture §7.3: lead sentence (`summary.description`, rendered
 * directly — it's already full-sentence prose from the backend), then
 * a compact stat row. `final_*_acc` are in [0, 1] — the backend
 * doesn't multiply by 100 for a percentage display (Integration Guide
 * §4), so this component does. `diverged` comes straight from the
 * backend, with a visible warning badge when true.
 */
export function SummaryPanel({ summary, isPolling }: SummaryPanelProps) {
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
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <p className="max-w-2xl text-sm text-foreground">{summary.description}</p>
        {summary.diverged && (
          <Badge tone="concern" icon={<AlertTriangle className="size-3.5" aria-hidden="true" />}>
            Diverged early
          </Badge>
        )}
      </div>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Final train loss" value={formatLoss(summary.final_train_loss)} />
        <StatCard label="Final val loss" value={formatLoss(summary.final_val_loss)} />
        <StatCard label="Final train acc" value={`${formatPercent(summary.final_train_acc)}%`} />
        <StatCard label="Final val acc" value={`${formatPercent(summary.final_val_acc)}%`} />
        <StatCard label="Wall-clock time" value={formatWallClock(summary.wall_clock_sec)} />
        <StatCard label="Epochs completed" value={summary.total_epochs_completed} />
        <StatCard label="Best val loss" value={formatLoss(summary.best_val_loss)} />
        <StatCard label="Best epoch" value={summary.best_epoch} />
      </div>
    </div>
  )
}
