import { useQuery, useQueries } from "@tanstack/react-query"
import { apiGet } from "@/lib/api/client"
import { endpoints } from "@/lib/api/endpoints"
import type { RunDetailResponse, RunComparisonResult } from "../types"

export const runKeys = {
  detail: (runId: string) => ["runs", runId] as const,
  comparison: (runAId: string, runBId: string) => ["runs", "compare", runAId, runBId] as const,
}

export function getRun(runId: string): Promise<RunDetailResponse> {
  return apiGet<RunDetailResponse>(endpoints.run(runId))
}

export function getRunComparison(runAId: string, runBId: string): Promise<RunComparisonResult> {
  return apiGet<RunComparisonResult>(endpoints.compareRuns(runAId, runBId))
}

/**
 * The query options for a single run — extracted so `useRunQuery`
 * (one run) and `useRunsQueries` (many runs, for `useExperimentSummary`)
 * share one definition of "how do we fetch/poll a run" instead of
 * duplicating the polling logic. `config` is effectively immutable
 * once written; `summary`/`diagnostics` can flip from `null` to
 * populated while a run is training, then never change again
 * (Integration Guide §7, Engineering Spec §6).
 */
function runQueryOptions(runId: string) {
  return {
    queryKey: runKeys.detail(runId),
    queryFn: () => getRun(runId),
    staleTime: 0,
    refetchInterval: (query: { state: { data?: RunDetailResponse } }) => {
      const data = query.state.data
      if (!data) return false
      const stillPending = data.summary === null || data.diagnostics === null
      return stillPending ? 7_000 : false
    },
  }
}

/**
 * GET /api/v1/runs/{runId} — the richest endpoint. Polling: enabled
 * only while either `summary` or `diagnostics` is still `null`, and
 * disabled the instant both are populated — a `null` result must
 * never be treated as a cached final answer.
 */
export function useRunQuery(runId: string) {
  return useQuery(runQueryOptions(runId))
}

/**
 * Fetches multiple runs at once via `useQueries` — the correct React
 * Query API for a dynamic-length array of queries (calling
 * `useRunQuery` in a loop would violate the Rules of Hooks, since the
 * number of runs isn't known at compile time). Shares the exact same
 * query key as `useRunQuery`, so this does NOT introduce a second,
 * separate fetch pattern: if `RunRow` has already fetched a given
 * run_id, this reads the same cache entry rather than re-fetching it,
 * and vice versa. Built for `useExperimentSummary` (aggregate stats
 * across every run in an experiment) — still the same N+1-by-design
 * pattern documented in Integration Guide §7/§9, just consumed by two
 * different call sites instead of one.
 */
export function useRunsQueries(runIds: string[]) {
  return useQueries({ queries: runIds.map(runQueryOptions) })
}

/**
 * GET /api/v1/runs/{a}/compare/{b} — fully deterministic and
 * side-effect-free (FRONTEND_INTEGRATION.md §1: "safe to call
 * repeatedly / cache client-side"), unlike the diagnose mutation.
 *
 * `staleTime: Infinity`, not just "long": run IDs are permanent and
 * never reused, and `diagnostics` — the only inputs this result is
 * computed from — are documented as immutable once non-null
 * (Integration Guide §7). For a given pair of run IDs there is no
 * future point where refetching could return a different answer, so
 * treating this as merely "low-churn" (the way `experiments` is,
 * with a 5-minute window) would be under-trusting the guarantee.
 *
 * Trade-off worth knowing: Infinity means this query no longer
 * refetches on window focus/reconnect the way every other query in
 * the app does (React Query only re-triggers those on stale queries).
 * That only matters if the backend's own immutability guarantee is
 * violated out-of-band (e.g. demo fixture data regenerated without a
 * page reload) — a narrow demo-prep risk, not a correctness one, and
 * a full reload resolves it.
 */
export function useRunComparisonQuery(runAId: string, runBId: string) {
  return useQuery({
    queryKey: runKeys.comparison(runAId, runBId),
    queryFn: () => getRunComparison(runAId, runBId),
    staleTime: Infinity,
  })
}