import { useQuery } from "@tanstack/react-query"
import { apiGet } from "@/lib/api/client"
import { endpoints } from "@/lib/api/endpoints"
import type { RunDetailResponse } from "../types"

export const runKeys = {
  detail: (runId: string) => ["runs", runId] as const,
}

export function getRun(runId: string): Promise<RunDetailResponse> {
  return apiGet<RunDetailResponse>(endpoints.run(runId))
}

/**
 * GET /api/v1/runs/{runId} — the richest endpoint. `config` is
 * effectively immutable once written; `summary`/`diagnostics` can
 * flip from `null` to populated while a run is training, then never
 * change again (Integration Guide §7, Engineering Spec §6).
 *
 * Polling: enabled only while either `summary` or `diagnostics` is
 * still `null`, and disabled the instant both are populated — a
 * `null` result must never be treated as a cached final answer.
 */
export function useRunQuery(runId: string) {
  return useQuery({
    queryKey: runKeys.detail(runId),
    queryFn: () => getRun(runId),
    staleTime: 0,
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data) return false
      const stillPending = data.summary === null || data.diagnostics === null
      return stillPending ? 7_000 : false
    },
  })
}
