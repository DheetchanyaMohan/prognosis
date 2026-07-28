import { TrendingUp, PauseCircle, Zap, CheckCircle2, Clock } from "lucide-react"
import { StatCard } from "@/components/ui"
import { formatLoss, formatPercent } from "@/features/runs"
import type { ExperimentSummary } from "../hooks/useExperimentSummary"

interface ExperimentSummaryCardsProps {
  summary: ExperimentSummary
}

/**
 * Every value here comes directly from `useExperimentSummary` — real
 * aggregation over actual run data, never an invented or estimated
 * figure. Icon choices deliberately match the ones `StatusBadge`
 * already uses for the same flags (TrendingUp/PauseCircle/Zap/
 * CheckCircle2), so a recruiter reading this page and a run row lower
 * down see the same visual vocabulary for "overfitting"/"stalled"/
 * "unstable"/"healthy" — one visual language, not two.
 */
export function ExperimentSummaryCards({ summary }: ExperimentSummaryCardsProps) {
  const dash = summary.isLoading ? "…" : "—"

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <StatCard label="Total Runs" value={summary.totalRuns} />
      <StatCard
        label="Healthy"
        value={summary.healthyCount}
        flag={<CheckCircle2 className="size-3.5 text-green-600 dark:text-green-400" aria-hidden="true" />}
      />
      <StatCard
        label="Overfitting"
        value={summary.overfittingCount}
        flag={<TrendingUp className="size-3.5 text-red-600 dark:text-red-400" aria-hidden="true" />}
      />
      <StatCard
        label="Unstable"
        value={summary.unstableCount}
        flag={<Zap className="size-3.5 text-red-600 dark:text-red-400" aria-hidden="true" />}
      />
      <StatCard
        label="Stalled"
        value={summary.stalledCount}
        flag={<PauseCircle className="size-3.5 text-amber-600 dark:text-amber-400" aria-hidden="true" />}
      />
      <StatCard
        label="Pending"
        value={summary.pendingCount}
        flag={<Clock className="size-3.5 text-blue-600 dark:text-blue-400" aria-hidden="true" />}
      />
      <StatCard
        label="Best Val Loss"
        value={summary.bestValLoss !== null ? formatLoss(summary.bestValLoss) : dash}
        sublabel={`of ${summary.completedRunsCount} completed`}
      />
      <StatCard
        label="Worst Val Loss"
        value={summary.worstValLoss !== null ? formatLoss(summary.worstValLoss) : dash}
        sublabel={`of ${summary.completedRunsCount} completed`}
      />
      <StatCard
        label="Avg Val Accuracy"
        value={summary.averageValAccuracy !== null ? `${formatPercent(summary.averageValAccuracy)}%` : dash}
        sublabel={`of ${summary.completedRunsCount} completed`}
      />
    </div>
  )
}