import { useMutation } from "@tanstack/react-query"
import { apiPost } from "@/lib/api/client"
import { endpoints } from "@/lib/api/endpoints"
import type { DiagnoseRequest, DiagnosisResponse } from "../types"

/** POST /runs/{id}/diagnose typically takes several seconds to ~30s (real LLM call) — far beyond the 10s default GET timeout. */
const DIAGNOSE_TIMEOUT_MS = 45_000

export function postDiagnoseRun(runId: string, request?: DiagnoseRequest): Promise<DiagnosisResponse> {
  return apiPost<DiagnosisResponse>(endpoints.diagnoseRun(runId), request, {
    timeoutMs: DIAGNOSE_TIMEOUT_MS,
  })
}

/**
 * POST /api/v1/runs/{runId}/diagnose — the only mutation in this app.
 * Invokes the LangGraph agent and is genuinely non-idempotent: two
 * calls for the same run can return different hypotheses/
 * recommendations (FRONTEND_INTEGRATION.md §1). `retry: false` is
 * deliberate — silently auto-retrying a real LLM call on transient
 * failure would be surprising and costly; a failed diagnosis instead
 * surfaces an explicit "try again" action that re-invokes `mutate()`.
 *
 * Nothing here is cached: the mutation's own `data`/`isPending`/
 * `error` state is the entire state model for the result — there is
 * no query key, because there is nothing to key a non-idempotent,
 * non-cacheable result by.
 */
export function useDiagnoseRunMutation() {
  return useMutation({
    mutationFn: ({ runId, request }: { runId: string; request?: DiagnoseRequest }) =>
      postDiagnoseRun(runId, request),
    retry: false,
  })
}