import { useRunsQueries, deriveRunStatus } from "@/features/runs"

export interface ExperimentSummary {
  totalRuns: number
  /** True while any underlying run query hasn't resolved yet — cards should show a loading state, not a wrong number. */
  isLoading: boolean
  /** Flags are independent booleans (a run can be both overfitting and unstable), so these counts are NOT mutually exclusive partitions of totalRuns — deliberately, since deriveRunStatus already treats them this way everywhere else in the app. */
  healthyCount: number
  overfittingCount: number
  unstableCount: number
  stalledCount: number
  /** Runs with no diagnostics yet (still training/not yet analyzed). */
  pendingCount: number
  /** Runs with a non-null summary — the denominator for the loss/accuracy stats below. */
  completedRunsCount: number
  bestValLoss: number | null
  worstValLoss: number | null
  averageValAccuracy: number | null
}

/**
 * Aggregates real data across every run in an experiment for the
 * Summary Cards (no invented statistics — every number here is
 * computed directly from actual `GET /api/v1/runs/{id}` responses).
 *
 * Uses `useRunsQueries` (React Query's `useQueries`), which shares the
 * exact same cache keys as each `RunRow`'s own `useRunQuery` call —
 * this does not introduce a second, separate fetch: if a row has
 * already loaded its run, this reads the same cached entry rather
 * than re-fetching it.
 *
 * Runs still loading or errored are excluded from every count (not
 * counted as "unhealthy" or folded into any category) — `isLoading`
 * tells the UI when the numbers are still incomplete.
 */
export function useExperimentSummary(runIds: string[]): ExperimentSummary {
  const queries = useRunsQueries(runIds)

  let healthyCount = 0
  let overfittingCount = 0
  let unstableCount = 0
  let stalledCount = 0
  let pendingCount = 0
  let completedRunsCount = 0
  let bestValLoss: number | null = null
  let worstValLoss: number | null = null
  let valAccuracySum = 0

  for (const query of queries) {
    const run = query.data
    if (!run) continue // still loading or errored — excluded, not miscategorized

    const flags = deriveRunStatus(run.diagnostics)
    if (flags.includes("healthy")) healthyCount++
    if (flags.includes("overfitting")) overfittingCount++
    if (flags.includes("unstable")) unstableCount++
    if (flags.includes("stalled")) stalledCount++
    if (flags.includes("pending")) pendingCount++

    if (run.summary) {
      completedRunsCount++
      const { best_val_loss, final_val_acc } = run.summary
      if (bestValLoss === null || best_val_loss < bestValLoss) bestValLoss = best_val_loss
      if (worstValLoss === null || best_val_loss > worstValLoss) worstValLoss = best_val_loss
      valAccuracySum += final_val_acc
    }
  }

  return {
    totalRuns: runIds.length,
    isLoading: queries.some((query) => query.isPending),
    healthyCount,
    overfittingCount,
    unstableCount,
    stalledCount,
    pendingCount,
    completedRunsCount,
    bestValLoss,
    worstValLoss,
    averageValAccuracy: completedRunsCount > 0 ? valAccuracySum / completedRunsCount : null,
  }
}