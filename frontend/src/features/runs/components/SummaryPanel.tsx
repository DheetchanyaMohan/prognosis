import { StatCard } from "@/components/ui"
import { formatWallClock, formatLoss, formatPercent } from "../utils/format-run-stats"
import type { RunSummaryResponse } from "../types"

interface SummaryPanelProps {
  summary: RunSummaryResponse | null
}

/**
 * Now scoped to ONLY the numeric stat grid — the prose description
 * and "diverged" badge moved to `RunOverviewSummary` (Overview
 * section) when Run Detail was restructured around 5 named sections
 * (Overview / AI Diagnosis / Metrics / Configuration / Detailed
 * Analysis). This component lives under "Metrics" now, alongside
 * `DiagnosisPanel`.
 *
 * `final_*_acc` are in [0, 1] — the backend doesn't multiply by 100
 * for a percentage display (Integration Guide §4), so this component
 * does. Renders nothing when `summary` is still `null`: the "still
 * training" messaging already lives in `RunOverviewSummary` above,
 * so a second "pending" card here would just be redundant.
 */
export function SummaryPanel({ summary }: SummaryPanelProps) {
  if (!summary) {
    return null
  }

  return (
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
  )
}